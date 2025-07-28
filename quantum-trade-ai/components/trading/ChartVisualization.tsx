"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Loader2, BarChart3, Download, TrendingUp, Calendar } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import axios from "axios"
import { XAxis, YAxis, CartesianGrid, Legend, LineChart, Line } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart" // Importar componentes de shadcn/ui/chart

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

  // Función para parsear CSV
  const parseCSV = (csvText: string) => {
    const lines = csvText.trim().split("\n")
    const headers = lines[0].split(",")

    return lines.slice(1).map((line) => {
      const values = line.split(",")
      const obj: any = {}

      headers.forEach((header, index) => {
        const cleanHeader = header.replace(/"/g, "").trim()
        const value = values[index]?.replace(/"/g, "").trim()

        if (cleanHeader === "Date") {
          obj[cleanHeader] = value
        } else {
          obj[cleanHeader] = Number.parseFloat(value) || 0
        }
      })

      return obj
    })
  }

  // Función para obtener datos reales del CSV
  const fetchRealData = async () => {
    setIsLoading(true)
    setLoadingState("Obteniendo datos reales del CSV...")

    try {
      const response = await fetch(
        "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/inference_GOOGL_e271e3cf-c54f-42d7-9f93-5a7305b93750%20%281%29-Dvr0AnTSc8qGgVDXHjmEoWQBN9SucU.csv",
      )
      const csvText = await response.text()

      console.log("CSV obtenido:", csvText.substring(0, 200) + "...")

      const parsedData = parseCSV(csvText)
      console.log("Datos parseados:", parsedData.slice(0, 3))

      setRealData(parsedData)
      setLoadingState("¡Datos reales cargados exitosamente!")
      onChartUpdate("", true)
    } catch (error) {
      console.error("Error al obtener CSV:", error)
      setLoadingState("Error al obtener datos del CSV")
    } finally {
      setTimeout(() => {
        setIsLoading(false)
        setLoadingState("")
      }, 2000)
    }
  }

  // Función para calcular retornos acumulativos (como en Python: np.exp(np.log1p(df).cumsum()) - 1)
  const calculateCumulativeReturns = (data) => {
    let strategySum = 0
    let buyHoldSum = 0

    return data.map((item, index) => {
      // Calcular log1p y suma acumulativa
      const strategyReturn = item["Strategy Return"] || 0
      const buyHoldReturn = item["GOOGL Buy&Hold"] || 0

      strategySum += Math.log1p(strategyReturn)
      buyHoldSum += Math.log1p(buyHoldReturn)

      // Calcular retorno acumulativo: exp(sum) - 1
      const strategyCumulative = Math.exp(strategySum) - 1
      const buyHoldCumulative = Math.exp(buyHoldSum) - 1

      return {
        date: new Date(item.Date).toLocaleDateString("en-US", { year: "2-digit", month: "2-digit" }), // Formato YY-MM
        fullDate: item.Date,
        strategyReturn: strategyCumulative, // Mantener como decimal para cálculo
        buyHoldReturn: buyHoldCumulative, // Mantener como decimal para cálculo
        strategyDaily: strategyReturn,
        buyHoldDaily: buyHoldReturn,
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
        const jsonResponse = await axios.get(plotUrl)
        const rawData = jsonResponse.data

        console.log("Datos de API recibidos:", rawData)
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
  const formattedData = dataToShow.length > 0 ? calculateCumulativeReturns(dataToShow) : []

  // Calcular métricas
  const finalStrategyReturn =
    formattedData.length > 0 ? (formattedData[formattedData.length - 1].strategyReturn * 100).toFixed(2) : "0"
  const finalBuyHoldReturn =
    formattedData.length > 0 ? (formattedData[formattedData.length - 1].buyHoldReturn * 100).toFixed(2) : "0"
  const totalDays = formattedData.length

  // Calcular métricas adicionales
  const calculateMetrics = (data) => {
    if (data.length === 0) return { volatility: "0", maxDrawdown: "0", sharpeRatio: "0" }

    const returns = data.map((d) => d.strategyDaily)
    const mean = returns.reduce((sum, val) => sum + val, 0) / returns.length
    const variance = returns.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / returns.length
    const volatility = Math.sqrt(variance * 252).toFixed(2) // Anualizada

    // Calcular máximo drawdown
    let maxDrawdown = 0
    let peak = 0
    data.forEach((d) => {
      const value = d.rawStrategyReturn
      if (value > peak) peak = value
      const drawdown = (peak - value) / peak
      if (drawdown > maxDrawdown) maxDrawdown = drawdown
    })

    // Sharpe ratio aproximado (asumiendo risk-free rate = 0)
    const sharpeRatio = volatility > 0 ? ((mean * Math.sqrt(252)) / Number.parseFloat(volatility)).toFixed(2) : "0"

    return {
      volatility,
      maxDrawdown: (maxDrawdown * 100).toFixed(2),
      sharpeRatio,
    }
  }

  const metrics = calculateMetrics(formattedData)

  // Determinar período de datos
  const startDate = formattedData.length > 0 ? formattedData[0].fullDate : ""
  const endDate = formattedData.length > 0 ? formattedData[formattedData.length - 1].fullDate : ""

  // Configuración para ChartContainer
  const chartConfig = {
    "Strategy Return": {
      label: "Strategy Return",
      color: "hsl(var(--chart-1))", // Usar color de shadcn/ui (naranja/rojo)
    },
    "GOOGL Buy&Hold": {
      label: "GOOGL Buy&Hold",
      color: "hsl(var(--chart-2))", // Usar color de shadcn/ui (azul)
    },
  }

  return (
    <Card className="bg-white text-slate-900 border-slate-200">
      {" "}
      {/* Fondo blanco */}
      <CardHeader>
        <CardTitle className="text-slate-900 flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-green-600" />
          Análisis de Trading GOOGL - Datos Reales
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
              <span className="text-slate-900 ml-2 font-bold">GOOGL</span>
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
            <div className="text-purple-600 font-bold text-xl">{metrics.volatility}%</div>
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
              <CartesianGrid strokeDasharray="3 3" stroke="#E0E0E0" /> {/* Color de grid más claro */}
              <XAxis
                dataKey="date"
                stroke="#616161" // Color de texto más oscuro
                fontSize={12}
                angle={-45}
                textAnchor="end"
                height={80}
                interval={Math.floor(formattedData.length / 10)}
              />
              <YAxis
                stroke="#616161" // Color de texto más oscuro
                fontSize={12}
                tickFormatter={(value) => `${value}%`} // Formato de porcentaje
                label={{
                  value: "Return",
                  angle: -90,
                  position: "insideLeft",
                  style: { textAnchor: "middle", fill: "#616161" },
                }}
              />
              <ChartTooltip
                cursor={false}
                content={
                  <ChartTooltipContent
                    className="bg-slate-900 text-white border-slate-700" // Fondo oscuro para tooltip
                    formatter={(value, name) => [
                      `${Number.parseFloat(value).toFixed(2)}%`,
                      name === "strategyReturn" ? "Strategy Return" : "GOOGL Buy&Hold",
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
                wrapperStyle={{ color: "#616161", paddingTop: "20px" }} // Color de texto más oscuro
                formatter={(value) => (value === "strategyReturn" ? "Strategy Return" : "GOOGL Buy&Hold")}
              />
              <Line
                type="monotone"
                dataKey="strategyReturn"
                stroke="hsl(var(--chart-1))" // Color de shadcn/ui
                strokeWidth={2}
                dot={false} // Sin puntos para coincidir con la imagen
              />
              <Line
                type="monotone"
                dataKey="buyHoldReturn"
                stroke="hsl(var(--chart-2))" // Color de shadcn/ui
                strokeWidth={2}
                dot={false} // Sin puntos para coincidir con la imagen
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
                <span className="text-slate-600">{metrics.volatility}%</span>
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
            <h4 className="text-blue-600 font-medium mb-3 flex items-center gap-2">📈 GOOGL Buy & Hold</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-600">Retorno Total:</span>
                <span className="text-blue-600 font-bold">{finalBuyHoldReturn}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Diferencia vs IA:</span>
                <span
                  className={`font-bold ${
                    Number.parseFloat(finalStrategyReturn) > Number.parseFloat(finalBuyHoldReturn)
                      ? "text-red-600"
                      : "text-green-600"
                  }`}
                >
                  {(Number.parseFloat(finalBuyHoldReturn) - Number.parseFloat(finalStrategyReturn)).toFixed(3)}%
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
                    Number.parseFloat(finalStrategyReturn) > Number.parseFloat(finalBuyHoldReturn)
                      ? "text-green-600"
                      : "text-blue-600"
                  }`}
                >
                  {Number.parseFloat(finalStrategyReturn) > Number.parseFloat(finalBuyHoldReturn)
                    ? "🚀 Estrategia IA"
                    : "📈 Buy & Hold"}
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
              link.download = "googl-trading-analysis.json"
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
              link.download = "googl-trading-analysis.csv"
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
