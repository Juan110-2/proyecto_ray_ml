"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Loader2, BarChart3, Download, TrendingUp, Calendar } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import axios from "axios"
import { XAxis, YAxis, CartesianGrid, Legend, LineChart, Line } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

interface ChartVisualizationProps {
  plotUrl: string
  inferenceData: any
  chartData: {
    imageSrc: string
    showImage: boolean
  }
  onChartUpdate: (imageSrc: string, showImage: boolean) => void
}

export default function ChartVisualization({
  plotUrl,
  inferenceData,
  chartData,
  onChartUpdate,
}: ChartVisualizationProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [loadingState, setLoadingState] = useState("")
  const [chartJsonData, setChartJsonData] = useState([])
  const [realData, setRealData] = useState([])
  const [ticker, setTicker] = useState("") // Para almacenar el ticker dinámico

  // Función para detectar el ticker y la columna de Buy&Hold
  const detectTickerAndColumns = (data: any[]) => {
    if (data.length === 0) return { ticker: "", buyHoldColumn: "" }
    
    const firstItem = data[0]
    const keys = Object.keys(firstItem)
    
    // Buscar la columna que contiene "Buy&Hold"
    const buyHoldColumn = keys.find(key => key.includes("Buy&Hold")) || ""
    
    // Extraer el ticker del nombre de la columna (ej: "ABT Buy&Hold" -> "ABT")
    const tickerMatch = buyHoldColumn.match(/^(.+?)\s+Buy&Hold$/)
    const detectedTicker = tickerMatch ? tickerMatch[1] : "STOCK"
    
    return { ticker: detectedTicker, buyHoldColumn }
  }

  // Función para obtener datos reales del CSV
  const fetchRealData = async () => {
    setIsLoading(true);
    setLoadingState("Obteniendo datos reales del servidor...");
  
    try {
      const response = await axios.post("http://localhost:8000/plot/", {
        url: plotUrl,
      });
  
      const parsedData = response.data;
      console.log("Datos recibidos:", parsedData.slice(0, 3));
      
      // Detectar ticker y columnas
      const { ticker: detectedTicker } = detectTickerAndColumns(parsedData);
      setTicker(detectedTicker);
  
      setRealData(parsedData);
      setLoadingState("¡Datos reales cargados exitosamente!");
      onChartUpdate("", true);
    } catch (error) {
      console.error("Error al obtener datos:", error);
      setLoadingState("Error al obtener datos del servidor");
    } finally {
      setTimeout(() => {
        setIsLoading(false);
        setLoadingState("");
      }, 2000);
    }
  };

  // Función para procesar datos (solo formatear, NO calcular)
  const processData = (data) => {
    const { buyHoldColumn } = detectTickerAndColumns(data)
    
    return data.map((item, index) => {
      // Los datos YA VIENEN como retornos acumulativos
      // Solo convertir a porcentaje para display
      const strategyCumulative = (item["Strategy Return"] || 0) * 100
      const buyHoldCumulative = (item[buyHoldColumn] || 0) * 100

      // Formatear la fecha correctamente
      const dateObj = new Date(item.date)
      const formattedDate = dateObj.toLocaleDateString("en-US", { 
        month: "2-digit",
        day: "2-digit",
        year: "2-digit"
      })

      return {
        date: formattedDate,
        fullDate: item.date,
        strategyReturn: strategyCumulative,
        buyHoldReturn: buyHoldCumulative,
        rawStrategyReturn: item["Strategy Return"], // Para métricas si las necesitas
        rawBuyHoldReturn: item[buyHoldColumn]
      }
    })
  }

  // Cargar datos reales al montar el componente
  useEffect(() => {
    fetchRealData()
  }, [])

  // Agregar useEffect para generar gráfica automáticamente cuando hay plotUrl
  useEffect(() => {
    const obtenerGrafica = async () => {
      if (!plotUrl) return

      setIsLoading(true)
      setLoadingState("Obteniendo datos de la API...")

      try {
        const jsonResponse = await axios.post("http://localhost:8000/plot/", {
          url: plotUrl,
        });
        
        const rawData = jsonResponse.data
        console.log("Datos de API recibidos:", rawData)
        
        // Detectar ticker y columnas
        const { ticker: detectedTicker } = detectTickerAndColumns(rawData);
        setTicker(detectedTicker);
        
        setChartJsonData(rawData)
        setLoadingState("¡Datos de API cargados exitosamente!")
        onChartUpdate("", true)
      } catch (error) {
        console.error("Error al obtener los datos de la API:", error)
        setLoadingState("Usando datos del CSV como respaldo")
      } finally {
        setTimeout(() => {
          setIsLoading(false)
          setLoadingState("")
        }, 2000)
      }
    }

    obtenerGrafica()
  }, [plotUrl])

  // Usar datos reales del CSV o datos de la API
  const dataToShow = chartJsonData.length > 0 ? chartJsonData : realData
  const formattedData = dataToShow.length > 0 ? processData(dataToShow) : []

  // Calcular métricas
  const finalStrategyReturn = formattedData.length > 0 ? formattedData[formattedData.length - 1].strategyReturn.toFixed(2) : "0"
  const finalBuyHoldReturn = formattedData.length > 0 ? formattedData[formattedData.length - 1].buyHoldReturn.toFixed(2) : "0"
  const totalDays = formattedData.length

  // Debug: Mostrar algunos valores para verificar
  if (formattedData.length > 0) {
    console.log("Primeros 3 valores formateados:", formattedData.slice(0, 3))
    console.log("Último valor Strategy:", finalStrategyReturn)
    console.log("Último valor Buy&Hold:", finalBuyHoldReturn)
  }

  // Calcular métricas básicas (simplificadas)
  const calculateMetrics = (data) => {
    if (data.length === 0) return { volatility: "N/A", maxDrawdown: "N/A", sharpeRatio: "N/A" }

    // Calcular máximo drawdown simple
    let maxDrawdown = 0
    let peak = -Infinity
    
    data.forEach((d) => {
      const value = d.rawStrategyReturn
      if (value > peak) peak = value
      const drawdown = peak > value ? peak - value : 0
      if (drawdown > maxDrawdown) maxDrawdown = drawdown
    })

    return {
      volatility: "N/A", // No calculamos sin retornos diarios
      maxDrawdown: (maxDrawdown * 100).toFixed(2),
      sharpeRatio: "N/A", // No calculamos sin retornos diarios
    }
  }

  const metrics = calculateMetrics(formattedData)

  // Determinar período de datos
  const startDate = formattedData.length > 0 ? formattedData[0].fullDate : ""
  const endDate = formattedData.length > 0 ? formattedData[formattedData.length - 1].fullDate : ""

  // Configuración para ChartContainer
  const chartConfig = {
    strategyReturn: {
      label: "Strategy Return",
      color: "hsl(var(--chart-1))",
    },
    buyHoldReturn: {
      label: `${ticker} Buy&Hold`,
      color: "hsl(var(--chart-2))",
    },
  }

  return (
    <Card className="bg-white text-slate-900 border-slate-200">
      <CardHeader>
        <CardTitle className="text-slate-900 flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-green-600" />
          Análisis de Trading {ticker} - Datos Reales
        </CardTitle>
        <CardDescription className="text-slate-600">
          Comparación de estrategias con datos reales de inferencia ({startDate} - {endDate})
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Estado de carga */}
        {isLoading && (
          <div className="p-4 bg-blue-100 border border-blue-300 rounded-lg">
            <div className="flex items-center gap-3">
              <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
              <span className="text-blue-600">{loadingState}</span>
            </div>
          </div>
        )}

        {/* Información del dataset */}
        <div className="p-4 bg-purple-100 border border-purple-300 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Calendar className="h-4 w-4 text-purple-600" />
            <span className="text-purple-600 font-medium">Dataset Information</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-slate-600">Ticker:</span>
              <span className="text-slate-900 ml-2 font-bold">{ticker}</span>
            </div>
            <div>
              <span className="text-slate-600">Período:</span>
              <span className="text-slate-900 ml-2">{totalDays} días</span>
            </div>
            <div>
              <span className="text-slate-600">Inicio:</span>
              <span className="text-slate-900 ml-2">{startDate}</span>
            </div>
            <div>
              <span className="text-slate-600">Fin:</span>
              <span className="text-slate-900 ml-2">{endDate}</span>
            </div>
          </div>
        </div>

        {/* Métricas principales */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="bg-slate-100 p-4 rounded-lg text-center">
            <div className="flex items-center justify-center mb-2">
              <TrendingUp className="h-5 w-5 text-green-600" />
            </div>
            <div className="text-green-600 font-bold text-xl">{finalStrategyReturn}%</div>
            <div className="text-slate-600 text-sm">Estrategia IA</div>
          </div>
          <div className="bg-slate-100 p-4 rounded-lg text-center">
            <div className="flex items-center justify-center mb-2">
              <TrendingUp className="h-5 w-5 text-blue-600" />
            </div>
            <div className="text-blue-600 font-bold text-xl">{finalBuyHoldReturn}%</div>
            <div className="text-slate-600 text-sm">Buy & Hold</div>
          </div>
          <div className="bg-slate-100 p-4 rounded-lg text-center">
            <div className="text-purple-600 font-bold text-xl">{metrics.volatility}</div>
            <div className="text-slate-600 text-sm">Volatilidad</div>
          </div>
          <div className="bg-slate-100 p-4 rounded-lg text-center">
            <div className="text-red-600 font-bold text-xl">{metrics.maxDrawdown}%</div>
            <div className="text-slate-600 text-sm">Max Drawdown</div>
          </div>
          <div className="bg-slate-100 p-4 rounded-lg text-center">
            <div className="text-yellow-600 font-bold text-xl">{metrics.sharpeRatio}</div>
            <div className="text-slate-600 text-sm">Sharpe Ratio</div>
          </div>
        </div>

        {/* Gráfica principal - Retornos Acumulativos */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Badge className="bg-green-600 text-white">Unsupervised Learning Trading Strategy Returns Over Time</Badge>
            <div className="text-slate-600 text-sm">{dataToShow.length} puntos de datos</div>
          </div>

          <ChartContainer config={chartConfig} className="min-h-[400px] w-full">
            <LineChart data={formattedData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E0E0E0" />
              <XAxis
                dataKey="date"
                stroke="#616161"
                fontSize={12}
                angle={-45}
                textAnchor="end"
                height={80}
                interval={Math.floor(formattedData.length / 10)}
              />
              <YAxis
                stroke="#616161"
                fontSize={12}
                tickFormatter={(value) => `${value.toFixed(1)}%`}
                domain={['dataMin', 'dataMax']}
                label={{
                  value: "Cumulative Return (%)",
                  angle: -90,
                  position: "insideLeft",
                  style: { textAnchor: "middle", fill: "#616161" },
                }}
              />
              <ChartTooltip
                cursor={false}
                content={
                  <ChartTooltipContent
                    className="bg-slate-900 text-white border-slate-700"
                    formatter={(value, name) => [
                      `${parseFloat(value).toFixed(2)}%`,
                      name === "strategyReturn" ? "Strategy Return" : `${ticker} Buy&Hold`,
                    ]}
                    labelFormatter={(label, payload) => {
                      if (payload && payload[0]) {
                        return `Date: ${payload[0].payload.fullDate}`
                      }
                      return `Date: ${label}`
                    }}
                  />
                }
              />
              <Legend
                wrapperStyle={{ color: "#616161", paddingTop: "20px" }}
                formatter={(value) => (value === "strategyReturn" ? "Strategy Return" : `${ticker} Buy&Hold`)}
              />
              <Line
                type="monotone"
                dataKey="buyHoldReturn"
                stroke="hsl(var(--chart-2))"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="strategyReturn"
                stroke="hsl(var(--chart-1))"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ChartContainer>
        </div>

        {/* Análisis estadístico detallado */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-slate-100 p-4 rounded-lg">
            <h4 className="text-green-600 font-medium mb-3 flex items-center gap-2">🚀 Estrategia IA</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-600">Retorno Total:</span>
                <span className="text-green-600 font-bold">{finalStrategyReturn}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Volatilidad Anual:</span>
                <span className="text-slate-600">{metrics.volatility}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Sharpe Ratio:</span>
                <span className="text-slate-600">{metrics.sharpeRatio}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Max Drawdown:</span>
                <span className="text-red-600">{metrics.maxDrawdown}%</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-100 p-4 rounded-lg">
            <h4 className="text-blue-600 font-medium mb-3 flex items-center gap-2">📈 {ticker} Buy & Hold</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-600">Retorno Total:</span>
                <span className="text-blue-600 font-bold">{finalBuyHoldReturn}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Diferencia vs IA:</span>
                <span
                  className={`font-bold ${
                    parseFloat(finalStrategyReturn) > parseFloat(finalBuyHoldReturn)
                      ? "text-red-600"
                      : "text-green-600"
                  }`}
                >
                  {(parseFloat(finalBuyHoldReturn) - parseFloat(finalStrategyReturn)).toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Período:</span>
                <span className="text-slate-600">{totalDays} días</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Ganador:</span>
                <span
                  className={`font-bold ${
                    parseFloat(finalStrategyReturn) > parseFloat(finalBuyHoldReturn)
                      ? "text-green-600"
                      : "text-blue-600"
                  }`}
                >
                  {parseFloat(finalStrategyReturn) > parseFloat(finalBuyHoldReturn)
                    ? "🚀 Estrategia IA"
                    : `📈 ${ticker} Buy & Hold`}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Botones de descarga */}
        <div className="flex gap-4 justify-center">
          <Button
            onClick={() => {
              const dataStr = JSON.stringify(formattedData, null, 2)
              const dataBlob = new Blob([dataStr], { type: "application/json" })
              const url = URL.createObjectURL(dataBlob)
              const link = document.createElement("a")
              link.href = url
              link.download = `${ticker.toLowerCase()}-trading-analysis.json`
              link.click()
            }}
            className="bg-purple-600 hover:bg-purple-700 text-white"
          >
            <Download className="h-4 w-4 mr-2" />
            Descargar JSON
          </Button>

          <Button
            onClick={() => {
              const csvContent = [
                "Date,Strategy Return (%),Buy&Hold Return (%),Strategy Cumulative (%),Buy&Hold Cumulative (%)",
                ...formattedData.map(
                  (d) => `${d.fullDate},${d.strategyDaily},${d.buyHoldDaily},${d.strategyReturn},${d.buyHoldReturn}`,
                ),
              ].join("\n")

              const dataBlob = new Blob([csvContent], { type: "text/csv" })
              const url = URL.createObjectURL(dataBlob)
              const link = document.createElement("a")
              link.href = url
              link.download = `${ticker.toLowerCase()}-trading-analysis.csv`
              link.click()
            }}
            className="bg-green-600 hover:bg-green-700 text-white"
          >
            <Download className="h-4 w-4 mr-2" />
            Descargar CSV
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}