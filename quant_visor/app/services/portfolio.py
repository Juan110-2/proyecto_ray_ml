from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import ray
import yfinance as yf
import pandas_ta
from sklearn.cluster import KMeans
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models, expected_returns
import statsmodels.api as sm
from statsmodels.regression.rolling import RollingOLS
import pandas_datareader.data as web
import warnings
import logging
from datetime import datetime
import time

# Configuración inicial
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Funciones auxiliares (las mismas que en tu código viejo)
def split_df_by_tickers(df, batch_size=10):
    tickers = df.columns.get_level_values(1).unique()
    ticker_batches = np.array_split(tickers, batch_size)
    return [df.loc[:, (slice(None), batch)] for batch in ticker_batches]

@ray.remote(memory=600*1024*1024)
def download_data_by_tickers(stocks,start,end):
    new_df = yf.download(tickers=stocks,
                        start=start,
                        end=end,auto_adjust=False)
    return new_df

@ray.remote(memory=600*1024*1024)
def calculate_tecnical_indicators(data):
        # df = copy.deepcopy(data)
        df=data
        df = df.stack()
        df.index.names = ['date', 'ticker']
        df.columns = df.columns.str.lower()
        # Calculate Garman-Klass Volatility
        df['garman_klass_vol'] = ((np.log(df['high']) - np.log(df['low']))**2)/2 - (2*np.log(2)-1)*((np.log(df['adj close']) - np.log(df['open']))**2)
        # Calculate RSI
        df['rsi'] = df.groupby(level=1)['adj close'].transform(lambda x: pandas_ta.rsi(close=x, length=20))
        def safe_bb_transform(x, col_idx):
            bb_result = pandas_ta.bbands(close=np.log1p(x), length=20)
            if bb_result is not None and len(bb_result.columns) > col_idx:
                return bb_result.iloc[:, col_idx]
            else:
                return pd.Series([np.nan] * len(x), index=x.index)
        df['bb_low'] = df.groupby(level=1)['adj close'].transform(lambda x: safe_bb_transform(x, 0))
        df['bb_mid'] = df.groupby(level=1)['adj close'].transform(lambda x: safe_bb_transform(x, 1))
        df['bb_high'] = df.groupby(level=1)['adj close'].transform(lambda x: safe_bb_transform(x, 2))
        # Calculate ATR
        def compute_atr(stock_data):
            atr = pandas_ta.atr(high=stock_data['high'],
                                low=stock_data['low'],
                                close=stock_data['close'],
                                length=14)
            if atr is not None:
                return atr.sub(atr.mean()).div(atr.std())
            else:
                return pd.Series([np.nan] * len(stock_data), index=stock_data.index)
        df['atr'] = df.groupby(level=1, group_keys=False).apply(compute_atr)
        # Calculate MACD
        def compute_macd(close):
            try:
                if len(close) < 35:  
                    return pd.Series([np.nan] * len(close), index=close.index)
                
                macd_result = pandas_ta.macd(close=close)  
                if macd_result is not None and not macd_result.empty:
                    macd = macd_result.iloc[:,0]
                    if macd.notna().sum() > 0:
                        return macd.sub(macd.mean()).div(macd.std())
                
                return pd.Series([np.nan] * len(close), index=close.index)
            except:
                return pd.Series([np.nan] * len(close), index=close.index)
        
        df['macd'] = df.groupby(level=1, group_keys=False)['adj close'].apply(compute_macd)
        
        # Calculate dollar volume
        df['dollar_volume'] = (df['adj close'] * df['volume']) / 1e6
        return df

@ray.remote(memory=600*1024*1024)
def Calculate_Montly_Returns(data):

  # To capture time series dynamics that reflect, for example,
  # momentum patterns, we compute historical returns using the method
  # .pct_change(lag), that is, returns over various monthly periods as identified by lags.

  data=data.stack()
  data.index.names=['date','ticker']
  data.columns=data.columns.str.lower()

  def calculate_returns(df):

    outlier_cutoff = 0.005

    lags = [1, 2, 3, 6, 9, 12]

    for lag in lags:

        df[f'return_{lag}m'] = (df['adj close']
                              .pct_change(lag)
                              .pipe(lambda x: x.clip(lower=x.quantile(outlier_cutoff),
                                                    upper=x.quantile(1-outlier_cutoff)))
                              .add(1)
                              .pow(1/lag)
                              .sub(1))
    return df


  data = data.groupby(level=1, group_keys=False).apply(calculate_returns).dropna()

  return data


@ray.remote(memory=600*1024*1024)
def calculate_rolling_f_betas(factor_data):
    factor_data=factor_data.stack()
    betas = (factor_data.groupby(level=1,
                            group_keys=False)
         .apply(lambda x: RollingOLS(endog=x['return_1m'], 
                                     exog=sm.add_constant(x.drop('return_1m', axis=1)),
                                     window=min(24, x.shape[0]),
                                     min_nobs=len(x.columns)+1)
         .fit(params_only=True)
         .params
         .drop('const', axis=1)))

    return betas


@ray.remote
def calculate_return_for_date(start_date, fixed_dates, new_df, returns_dataframe):
    
    try:
        end_date = (pd.to_datetime(start_date)+pd.offsets.MonthEnd(0)).strftime('%Y-%m-%d')
        cols = fixed_dates[start_date]
        optimization_start_date = (pd.to_datetime(start_date)-pd.DateOffset(months=12)).strftime('%Y-%m-%d')
        optimization_end_date = (pd.to_datetime(start_date)-pd.DateOffset(days=1)).strftime('%Y-%m-%d')

        optimization_df = new_df[optimization_start_date:optimization_end_date]['Adj Close'][cols]

        try:
            weights = optimize_weights(prices=optimization_df,
                                  lower_bound=round(1/(len(optimization_df.columns)*2),3))
            weights = pd.DataFrame(weights, index=optimization_df.columns, columns=[0])
        except:
            weights = pd.DataFrame([1/len(optimization_df.columns) for _ in range(len(optimization_df.columns))],
                                   index=optimization_df.columns.tolist(),
                                   columns=[0])

        temp_df = returns_dataframe[start_date:end_date][cols]
        portfolio_returns = [
            sum(temp_df.loc[date, t] * weights.loc[t, 0] for t in temp_df.columns if pd.notna(temp_df.loc[date, t]) and t in weights.index)
            for date in temp_df.index
        ]
        return pd.DataFrame(portfolio_returns, index=temp_df.index, columns=['Strategy Return'])

    except Exception as e:
        print(f"Error for {start_date}: {e}")
        return pd.DataFrame()

class PortfolioOptimizer:
    """Clase completa con todos los métodos necesarios"""
    
    def __init__(self, symbols_list: List[str], start_date: str, end_date: str):
        self.symbols_list = self._validate_symbols(symbols_list)
        self.start_date = start_date
        self.end_date = end_date
        self._validate_dates()

    def _validate_symbols(self, symbols: List[str]) -> List[str]:
        if not symbols:
            raise ValueError("La lista de símbolos no puede estar vacía")
        return [s for s in symbols if isinstance(s, str) and s.strip()]

    def _validate_dates(self):
        if pd.to_datetime(self.start_date) >= pd.to_datetime(self.end_date):
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")

    def load_data(self, batch_size: int = 10) -> pd.DataFrame:
        logger.info("Cargando datos de precios...")
        try:
            ticker_batches = np.array_split(self.symbols_list, min(batch_size, len(self.symbols_list)))
            futures = [download_data_by_tickers.remote(batch.tolist(), self.start_date, self.end_date) for batch in ticker_batches]
            results = ray.get(futures)
            
            # Verificar que los datos descargados tengan las columnas esperadas
            for df in results:
                if df.empty:
                    logger.warning("Se recibió un DataFrame vacío de yfinance")
                else:
                    required_columns = ['High', 'Low', 'Close', 'Open', 'Volume']
                    for col in required_columns:
                        if col not in df.columns:
                            logger.warning(f"Faltante columna {col} en datos descargados. Columnas disponibles: {df.columns.tolist()}")
            
            combined = pd.concat([r for r in results if not r.empty], axis=1)
            
            # Verificar que tenemos datos antes de continuar
            if combined.empty:
                raise ValueError("No se pudieron descargar datos de Yahoo Finance para los símbolos proporcionados")
                
            return combined
        except Exception as e:
            logger.error(f"Error al cargar datos: {str(e)}")
            raise

    
    def calculate_tecnical_indicators_p(self,data,batch_size=10):
        print("📊 Calculando indicadores técnicos...")
        batches=split_df_by_tickers(data,batch_size)
        futures=[calculate_tecnical_indicators.remote(df) for df in batches]
        results = ray.get(futures)
        df_indicators=pd.concat(results)
        print("✅ Indicadores técnicos calculados.")
        return df_indicators

    def aggregate_to_monthly_level(self,df):
        print("📆 Agregando a nivel mensual...")
        last_cols = [c for c in df.columns.unique(0) if c not in ['dollar_volume', 'volume', 'open',
                                                                'high', 'low', 'close']]
    
        data = (pd.concat([df.unstack('ticker')['dollar_volume'].resample('M').mean().stack('ticker').to_frame('dollar_volume'),
                        df.unstack()[last_cols].resample('M').last().stack('ticker')],
                        axis=1)).dropna()
    
        data['dollar_volume'] = (data.loc[:, 'dollar_volume'].unstack('ticker').rolling(5*12, min_periods=12).mean().stack())
    
        data['dollar_vol_rank'] = (data.groupby('date')['dollar_volume'].rank(ascending=False))
    
        data = data[data['dollar_vol_rank']<150].drop(['dollar_volume', 'dollar_vol_rank'], axis=1)
        print("✅ Agregación mensual completada.")
        return data

    def calculate_monthly_returns_p(self,df_aggregate,batch_size=10):
        print("📈 Calculando retornos mensuales...")
        df= df_aggregate.unstack()
        batches=split_df_by_tickers(df,batch_size)
        futures=[Calculate_Montly_Returns.remote(df) for df in batches]
        results=ray.get(futures)
        monthly_returns=pd.concat(results)
        print("✅ Retornos mensuales calculados.")
        return monthly_returns

    def download_fama_french_factors(self,montly_returns):
        print("📥 Descargando factores de Fama-French...")
        data=montly_returns
        factor_data = web.DataReader('F-F_Research_Data_5_Factors_2x3',
                                   'famafrench',
                                   start='2010')[0].drop('RF', axis=1)
        factor_data.index = factor_data.index.to_timestamp()
        factor_data = factor_data.resample('M').last().div(100)
        factor_data.index.name = 'date'
        factor_data = factor_data.join(data['return_1m']).sort_index()
        observations = factor_data.groupby(level=1).size()
        valid_stocks = observations[observations >= 10]
        factor_data = factor_data[factor_data.index.get_level_values('ticker').isin(valid_stocks.index)]
        print("✅ Factores descargados.")    
        return factor_data

    def calculate_rolling_betas(self,factor_data,batch_size=10):
        print("📊 Calculando betas de Fama-French en paralelo...")    
        fd=factor_data.unstack()
        factor_batches=split_df_by_tickers(fd,batch_size)
        start_time=time.time()
        futures=[calculate_rolling_f_betas.remote(fb) for fb in factor_batches]
        results=ray.get(futures)
        df=pd.concat(results)
        return df

    def join_factors(self,montly_returns,df_betas):
        print("🔗 Uniendo factores R a las características principales...")
        betas=df_betas
        data=montly_returns
        factors = ['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA']
        data = (data.join(betas.groupby('ticker').shift()))
        data.loc[:, factors] = data.groupby('ticker', group_keys=False)[factors].apply(lambda x: x.fillna(x.mean()))
        data = data.drop('adj close', axis=1)
        data = data.dropna()
        return data
    
    def apply_clustering(self,join_data):
        print("🤖 Aplicando KMeans con centroides predefinidos...")
        data=join_data
        target_rsi_values = [30, 45, 55, 70]
        initial_centroids = np.zeros((len(target_rsi_values), 18))
        initial_centroids[:, 6] = target_rsi_values
        def get_clusters(df):
          df['cluster'] = KMeans(n_clusters=4,
                                random_state=0,
                                init=initial_centroids).fit(df).labels_
          return df
        data = data.dropna().groupby('date', group_keys=False).apply(get_clusters)
        return data

    def apply_pre_defined_centroids_kmeans(self,join_data):
        print("🤖 Aplicando KMeans con centroides predefinidos...")
        data=join_data
        target_rsi_values = [30, 45, 55, 70]
        initial_centroids = np.zeros((len(target_rsi_values), 18))
        initial_centroids[:, 6] = target_rsi_values
        def get_clusters(df):
          df['cluster'] = KMeans(n_clusters=4,
                                random_state=0,
                                init=initial_centroids).fit(df).labels_
          return df
        data = data.dropna().groupby('date', group_keys=False).apply(get_clusters)
        return data

    def build_portfolio(self,cluster_data):
        print("📊 Creando portafolio basado en el cluster 3...")       
        data=cluster_data
        filtered_df = data[data['cluster']==3].copy()
        filtered_df = filtered_df.reset_index(level=1)
        filtered_df.index = filtered_df.index+pd.DateOffset(1)
        filtered_df = filtered_df.reset_index().set_index(['date', 'ticker'])
        dates = filtered_df.index.get_level_values('date').unique().tolist()
        fixed_dates = {}
        for d in dates:
            fixed_dates[d.strftime('%Y-%m-%d')] = filtered_df.xs(d, level=0).index.tolist()
        return fixed_dates

    def download_recent_prices(self,clusters_data,batch_size=10):
        print("📥 Cargando datos de precios diarios en paralelo..." )
        data=clusters_data.stack()
        start=data.index.get_level_values('date').unique()[0]-pd.DateOffset(months=12)
        end=data.index.get_level_values('date').unique()[-1]
        stocks = data.index.get_level_values('ticker').unique().tolist()
        ticker_batches=np.array_split(stocks,batch_size)
        futures=[download_data_by_tickers.remote(batch.tolist(),start,end) for batch in ticker_batches]
        results=ray.get(futures)
        new_df=pd.concat(results,axis=1)
        return new_df

    def calculate_portfolio_returns(self, new_df: pd.DataFrame, fixed_dates: Dict[str, List[str]]) -> pd.DataFrame:
        print("📈 Calculando retornos del portafolio para cada fecha...")
        returns_dataframe = np.log(new_df['Adj Close']).diff()
        futures = [
        calculate_return_for_date.remote(start_date, fixed_dates, new_df, returns_dataframe)
        for start_date in fixed_dates.keys()
        ]
        results = ray.get(futures)
        portfolio_df = pd.concat(results).drop_duplicates()
        return portfolio_df

    @staticmethod
    def _optimize_weights(prices: pd.DataFrame, lower_bound: float = 0) -> Dict[str, float]:
        try:
            returns = expected_returns.mean_historical_return(prices=prices, frequency=252)
            cov = risk_models.sample_cov(prices=prices, frequency=252)
            ef = EfficientFrontier(returns, cov, weight_bounds=(lower_bound, 0.1), solver='SCS')
            return ef.max_sharpe()
        except:
            n = len(prices.columns)
            return {ticker: 1/n for ticker in prices.columns}

    def optimize(self, batch_size: int = 10) -> pd.DataFrame:
        """Método principal que ejecuta todo el pipeline"""
        logger.info("Iniciando optimización de portafolio...")
        try:
            # Pipeline completo con manejo de errores
            price_data = self.load_data(batch_size)
            if price_data.empty:
                raise ValueError("No se obtuvieron datos de precios válidos")
            
            indicators = self.calculate_tecnical_indicators_p(price_data, batch_size)
            monthly_data = self.aggregate_to_monthly_level(indicators)
            returns = self.calculate_monthly_returns_p(monthly_data, batch_size)
            factor_data = self.download_fama_french_factors(returns)
            betas = self.calculate_rolling_betas(factor_data, batch_size)
            merged_data = self.join_factors(returns, betas)
            clustered_data = self.apply_clustering(merged_data)
            
            portfolio = self.build_portfolio(clustered_data)
            recent_prices = self.download_recent_prices(clustered_data, batch_size)
            portfolio_returns = self.calculate_portfolio_returns(recent_prices, portfolio)
            
            return portfolio_returns.sort_index()
        except Exception as e:
            logger.error(f"Error en el pipeline de optimización: {str(e)}")
            raise

