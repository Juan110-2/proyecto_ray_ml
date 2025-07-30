import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
import emoji
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import ray


nltk.download('stopwords')
nltk.download('wordnet')

logger = logging.getLogger(__name__)

@ray.remote(memory=600*1024*1024)
def process_tweet_batch(tweets: List[str]) -> List[Dict]:
    """Procesa un batch de tweets en paralelo"""
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    processed = []
    
    for text in tweets:
        try:
            # Limpieza básica
            text = text.lower()
            text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
            text = re.sub(r'@\w+|#\w+', '', text)
            text = emoji.demojize(text)
            text = re.sub(r':[a-z_]+:', '', text)
            text = re.sub(r'[^a-zA-Z\s]', '', text)
            
            # Lemmatización
            words = [lemmatizer.lemmatize(word) for word in text.split() 
                    if word not in stop_words and len(word) > 2]
            
            processed.append(' '.join(words).strip())
        except Exception as e:
            logger.warning(f"Error processing tweet: {str(e)}")
            processed.append('')
    
    return processed

class TwitterSentimentAnalyzer:
    """
    Servicio avanzado para análisis de sentimiento en Twitter que:
    1. Procesa datos de tweets en paralelo
    2. Realiza análisis de sentimiento
    3. Genera señales para optimización de portafolio
    
    Args:
        df: DataFrame con datos de tweets (debe contener columns: date, symbol, text, twitterComments, twitterLikes)
    """

    def __init__(self, df: pd.DataFrame):
        """Valida e inicializa con datos de Twitter"""
        self.df = self._validate_input(df)
        self._setup_pipelines()
        logger.info("TwitterSentimentAnalyzer initialized with %d tweets", len(df))

    def _validate_input(self, df: pd.DataFrame) -> pd.DataFrame:
        """Valida las columnas requeridas y tipos de datos"""
        required_cols = {
            'date': 'datetime64[ns]',
            'symbol': 'object',
            'text': 'object',
            'twitterComments': 'int64',
            'twitterLikes': 'int64'
        }
        
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
            
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        return df

    def _setup_pipelines(self):
        """Configura los pipelines de procesamiento"""
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=stopwords.words('english')
        )
        
    def filter_by_engagement(self, min_likes: int = 20, min_comments: int = 10) -> pd.DataFrame:
        """Filtra tweets por umbrales de engagement"""
        filtered = self.df[
            (self.df['twitterLikes'] >= min_likes) & 
            (self.df['twitterComments'] >= min_comments)
        ].copy()
        
        if filtered.empty:
            raise ValueError("No tweets meet the engagement thresholds")
            
        logger.info("Filtered %d tweets by engagement", len(filtered))
        return filtered

    def preprocess_tweets(self, df: pd.DataFrame, batch_size: int = 100) -> pd.DataFrame:
        """Procesa tweets en paralelo usando Ray"""
        tweets = df['text'].tolist()
        batches = [tweets[i:i + batch_size] for i in range(0, len(tweets), batch_size)]
        
        futures = [process_tweet_batch.remote(batch) for batch in batches]
        results = ray.get(futures)
        
        cleaned_texts = [text for batch in results for text in batch]
        df['cleaned_text'] = cleaned_texts
        
        # Eliminar tweets vacíos
        initial_count = len(df)
        df = df[df['cleaned_text'].str.len() > 0]
        logger.info("Removed %d empty tweets after cleaning", initial_count - len(df))
        
        return df

    def analyze_sentiment(self, df: pd.DataFrame) -> pd.DataFrame:
        """Analiza sentimiento usando TextBlob y transformers"""
        # Sentimiento básico con TextBlob
        df['sentiment'] = df['cleaned_text'].apply(
            lambda x: TextBlob(x).sentiment.polarity
        )
        
        # Clasificación binaria
        df['sentiment_label'] = np.where(df['sentiment'] > 0, 'positive', 'negative')
        
        logger.info("Sentiment distribution:\n%s", df['sentiment_label'].value_counts())
        return df

    def cluster_tweets(self, df: pd.DataFrame, n_clusters: int = 5) -> pd.DataFrame:
        """Agrupa tweets por temas usando K-Means"""
        try:
            tfidf = self.vectorizer.fit_transform(df['cleaned_text'])
            df['topic'] = KMeans(n_clusters=n_clusters).fit_predict(tfidf)
            return df
        except Exception as e:
            logger.error("Clustering failed: %s", str(e))
            return df

    def generate_portfolio_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Genera señales para el portafolio basado en:
        - Sentimiento promedio por símbolo
        - Engagement relativo
        - Diversificación por temas
        """
        signals = df.groupby(['date', 'symbol']).agg({
            'sentiment': 'mean',
            'twitterLikes': 'sum',
            'twitterComments': 'sum',
            'topic': lambda x: x.mode()[0] if 'topic' in df.columns else 0
        }).reset_index()
        
        # Normalizar engagement
        signals['engagement'] = (
            signals['twitterLikes'] + signals['twitterComments'] * 2
        )
        signals['engagement'] = signals['engagement'] / signals['engagement'].max()
        
        # Puntaje compuesto
        signals['score'] = (
            signals['sentiment'] * 0.6 + 
            signals['engagement'] * 0.4
        )
        
        return signals

    def full_pipeline(self, min_likes: int = 20, min_comments: int = 10) -> pd.DataFrame:
        """
        Pipeline completo para generar retornos de portafolio:
        1. Filtrado por engagement
        2. Preprocesamiento de texto
        3. Análisis de sentimiento
        4. Agrupamiento por temas (opcional)
        5. Generación de señales
        6. Cálculo de retornos
        """
        try:

            filtered = self.filter_by_engagement(min_likes, min_comments)
            
            processed = self.preprocess_tweets(filtered)
            
            analyzed = self.analyze_sentiment(processed)
            
            if len(analyzed) > 100:
                analyzed = self.cluster_tweets(analyzed)
            
            signals = self.generate_portfolio_signals(analyzed)
            
            portfolio_returns = self._calculate_returns(signals)
            
            return portfolio_returns
            
        except Exception as e:
            logger.error("Pipeline failed: %s", str(e), exc_info=True)
            raise

    def _calculate_returns(self, signals: pd.DataFrame) -> pd.DataFrame:
        """Implementa tu lógica específica para calcular retornos"""
        returns = signals.groupby('date').apply(
            lambda x: np.average(x['score'], weights=x['engagement'])
        ).to_frame('strategy_return')
        
        returns.index = pd.to_datetime(returns.index)
        return returns

def save_twitter_results(df: pd.DataFrame, path: str) -> None:
    """Guarda resultados en formato parquet"""
    try:
        df.to_parquet(path)
        logger.info("Results saved to %s", path)
    except Exception as e:
        logger.error("Error saving results: %s", str(e))
        raise

def load_twitter_results(path: str) -> pd.DataFrame:
    """Carga resultados desde parquet"""
    try:
        return pd.read_parquet(path)
    except Exception as e:
        logger.error("Error loading results: %s", str(e))
        raise