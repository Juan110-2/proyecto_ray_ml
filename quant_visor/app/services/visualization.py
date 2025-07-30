import logging
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Union
from datetime import datetime
from plotly.subplots import make_subplots
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from ray import serve

# Configuración de logging
logger = logging.getLogger(__name__)

# --------------------------
# Clase Principal
# --------------------------

@serve.deployment
class FinancialVisualizer:
    """
    Servicio para visualización de datos financieros con capacidades de:
    - Gráficos interactivos de series temporales
    - Análisis de rendimiento
    - Visualización de riesgo
    - Reportes personalizados
    """

    def __init__(self):
        self._setup_themes()
        logger.info("FinancialVisualizer initialized")

    def _setup_themes(self):
        """Configura temas y estilos visuales"""
        self.theme = {
            'colorway': ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A'],
            'template': 'plotly_white',
            'font_family': 'Arial',
            'title_font_size': 20,
            'legend_font_size': 14
        }

    # --------------------------
    # Métodos Básicos de Visualización
    # --------------------------

    def plot_returns(self, 
                    returns: pd.Series, 
                    title: str = "Rendimiento Acumulado",
                    benchmark: Optional[pd.Series] = None) -> go.Figure:
        """
        Crea gráfico de rendimiento acumulado con opción de benchmark.
        
        Args:
            returns: Serie de retornos diarios
            title: Título del gráfico
            benchmark: Serie de retornos del benchmark
            
        Returns:
            Figure de Plotly
        """
        try:
            cumulative_returns = (1 + returns).cumprod() - 1
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=cumulative_returns.index,
                y=cumulative_returns,
                mode='lines',
                name='Estrategia',
                line=dict(width=2.5)
            ))

            if benchmark is not None:
                benchmark_cumulative = (1 + benchmark).cumprod() - 1
                fig.add_trace(go.Scatter(
                    x=benchmark_cumulative.index,
                    y=benchmark_cumulative,
                    mode='lines',
                    name='Benchmark',
                    line=dict(width=2, dash='dot')
                ))

            fig.update_layout(
                title=title,
                yaxis_title='Rendimiento Acumulado',
                xaxis_title='Fecha',
                hovermode='x unified',
                **self.theme
            )

            fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="grey")

            return fig

        except Exception as e:
            logger.error(f"Error plotting returns: {str(e)}")
            raise

    # --------------------------
    # Métodos Avanzados
    # --------------------------

    def plot_risk_metrics(self,
                         returns: pd.Series,
                         window: int = 21) -> go.Figure:
        """
        Crea gráfico combinado de métricas de riesgo.
        
        Args:
            returns: Serie de retornos diarios
            window: Ventana para cálculos rolling
            
        Returns:
            Figure con subplots de métricas
        """
        try:
            rolling_vol = returns.rolling(window).std() * np.sqrt(252)
            rolling_sharpe = (returns.rolling(window).mean() / returns.rolling(window).std()) * np.sqrt(252)
            drawdown = (1 + returns).cumprod() / (1 + returns).cumprod().cummax() - 1

            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=('Volatilidad Anualizada', 'Ratio de Sharpe', 'Drawdown'),
                vertical_spacing=0.1
            )

            fig.add_trace(
                go.Scatter(
                    x=rolling_vol.index,
                    y=rolling_vol,
                    name='Volatilidad',
                    line=dict(color='#EF553B')
                ),
                row=1, col=1
            )

            fig.add_trace(
                go.Scatter(
                    x=rolling_sharpe.index,
                    y=rolling_sharpe,
                    name='Sharpe',
                    line=dict(color='#00CC96')
                ),
                row=2, col=1
            )

            fig.add_trace(
                go.Scatter(
                    x=drawdown.index,
                    y=drawdown,
                    fill='tozeroy',
                    name='Drawdown',
                    line=dict(color='#AB63FA')
                ),
                row=3, col=1
            )

            fig.update_layout(
                height=800,
                showlegend=False,
                title_text='Métricas de Riesgo',
                **self.theme
            )

            fig.update_yaxes(title_text="Volatilidad", row=1, col=1)
            fig.update_yaxes(title_text="Sharpe Ratio", row=2, col=1)
            fig.update_yaxes(title_text="Drawdown", row=3, col=1)

            return fig

        except Exception as e:
            logger.error(f"Error plotting risk metrics: {str(e)}")
            raise

    # --------------------------
    # Visualización de Portafolios
    # --------------------------

    def plot_portfolio_composition(self,
                                 weights: Dict[str, float],
                                 title: str = "Composición del Portafolio") -> go.Figure:
        """
        Gráfico de torta con la composición del portafolio.
        
        Args:
            weights: Diccionario con {activo: peso}
            title: Título del gráfico
            
        Returns:
            Figure de Plotly
        """
        try:
            df = pd.DataFrame.from_dict(weights, orient='index', columns=['weight'])
            df = df.sort_values('weight', ascending=False)
            
            if len(df) > 10:
                others = df[10:].sum()
                df = df[:10]
                df.loc['Otros'] = others

            fig = go.Figure(go.Pie(
                labels=df.index,
                values=df['weight'],
                textinfo='percent+label',
                insidetextorientation='radial',
                hole=0.3
            ))

            fig.update_layout(
                title=title,
                **self.theme
            )

            return fig

        except Exception as e:
            logger.error(f"Error plotting portfolio composition: {str(e)}")
            raise

    # --------------------------
    # Métodos para Reportes
    # --------------------------

    def generate_performance_report(self,
                                  returns: pd.Series,
                                  benchmark: Optional[pd.Series] = None) -> Dict[str, str]:
        """
        Genera reporte completo con visualizaciones en formato HTML/base64.
        
        Args:
            returns: Serie de retornos de la estrategia
            benchmark: Serie de retornos del benchmark
            
        Returns:
            Diccionario con gráficos en formato base64 y métricas
        """
        try:
            report = {}
            
            returns_fig = self.plot_returns(returns, benchmark=benchmark)
            risk_fig = self.plot_risk_metrics(returns)
            
            report['returns_chart'] = self._fig_to_base64(returns_fig)
            report['risk_chart'] = self._fig_to_base64(risk_fig)
            
            report['metrics'] = self._calculate_performance_metrics(returns, benchmark)
            
            return report

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise

    def _fig_to_base64(self, fig: go.Figure) -> str:
        """Convierte figura Plotly a base64 para incrustar en HTML"""
        img_bytes = fig.to_image(format="png")
        return base64.b64encode(img_bytes).decode('utf-8')

    def _calculate_performance_metrics(self,
                                    returns: pd.Series,
                                    benchmark: Optional[pd.Series] = None) -> Dict:
        """Calcula métricas clave de performance"""
        metrics = {
            'annualized_return': returns.mean() * 252,
            'annualized_volatility': returns.std() * np.sqrt(252),
            'sharpe_ratio': returns.mean() / returns.std() * np.sqrt(252),
            'max_drawdown': (returns.cumsum().expanding().max() - returns.cumsum()).max()
        }
        
        if benchmark is not None:
            metrics['alpha'] = returns.mean() - benchmark.mean()
            metrics['beta'] = returns.cov(benchmark) / benchmark.var()
            
        return metrics

    # --------------------------
    # Visualización Técnica
    # --------------------------

    def plot_autocorrelation(self,
                            returns: pd.Series,
                            lags: int = 30) -> str:
        """
        Gráfico de autocorrelación (ACF y PACF) en base64.
        
        Args:
            returns: Serie de retornos
            lags: Número de lags a mostrar
            
        Returns:
            Imagen en base64
        """
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            plot_acf(returns, lags=lags, ax=ax1)
            ax1.set_title('Autocorrelación (ACF)')
            
            plot_pacf(returns, lags=lags, ax=ax2)
            ax2.set_title('Autocorrelación Parcial (PACF)')
            
            plt.tight_layout()
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            plt.close()
            
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error plotting autocorrelation: {str(e)}")
            raise

# --------------------------
# Funciones de Utilidad
# --------------------------

def save_plot(fig: go.Figure, filename: str, format: str = 'html') -> None:
    """
    Guarda gráfico en diferentes formatos.
    
    Args:
        fig: Figura de Plotly
        filename: Nombre del archivo (sin extensión)
        format: Formato ('html', 'png', 'jpeg', 'svg')
    """
    try:
        if format == 'html':
            fig.write_html(f"{filename}.html")
        else:
            fig.write_image(f"{filename}.{format}")
            
        logger.info(f"Plot saved as {filename}.{format}")
    except Exception as e:
        logger.error(f"Error saving plot: {str(e)}")
        raise

def load_plot(filepath: str) -> go.Figure:
    """
    Carga gráfico desde archivo HTML.
    
    Args:
        filepath: Ruta al archivo HTML
        
    Returns:
        Figure de Plotly
    """
    try:
        return go.Figure.from_html(filepath)
    except Exception as e:
        logger.error(f"Error loading plot: {str(e)}")
        raise