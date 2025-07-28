"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { TrendingUp, Brain, Zap, BarChart3, RotateCcw, AlertTriangle } from "lucide-react"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import IndexSelector from "@/components/trading/IndexSelector"
import ModelTrainer from "@/components/trading/ModelTrainer"
import InferenceEngine from "@/components/trading/InferenceEngine"
import ChartVisualization from "@/components/trading/ChartVisualization"

export default function QuantumTradeAI() {
  // Estados principales
  const [activeTab, setActiveTab] = useState("index")
  const [selectedIndex, setSelectedIndex] = useState("")
  const [isTrained, setIsTrained] = useState(false)
  const [inferenceData, setInferenceData] = useState(null)
  const [plotUrl, setPlotUrl] = useState("")

  // Estados del entrenamiento
  const [trainingData, setTrainingData] = useState({
    startDate: "",
    endDate: "",
    batchSize: "32",
  })

  // Estados de la inferencia
  const [inferenceConfig, setInferenceConfig] = useState({
    ticker: "",
    startDateIn: "",
    endDateIn: "",
  })

  // Estados de visualización
  const [chartData, setChartData] = useState({
    imageSrc: "",
    showImage: false,
  })

  // Función para reiniciar toda la aplicación
  const handleReset = () => {
    // Resetear todos los estados
    setActiveTab("index")
    setSelectedIndex("")
    setIsTrained(false)
    setInferenceData(null)
    setPlotUrl("")

    // Resetear datos de entrenamiento
    setTrainingData({
      startDate: "",
      endDate: "",
      batchSize: "32",
    })

    // Resetear configuración de inferencia
    setInferenceConfig({
      ticker: "",
      startDateIn: "",
      endDateIn: "",
    })

    // Resetear datos de visualización
    setChartData({
      imageSrc: "",
      showImage: false,
    })
  }

  // Función para manejar la finalización del entrenamiento
  const handleTrainingComplete = (success: boolean) => {
    setIsTrained(success)
    if (success) {
      // Automáticamente cambiar al siguiente tab
      setTimeout(() => setActiveTab("inference"), 1000)
    }
  }

  // Función para manejar la finalización de la inferencia
  const handleInferenceComplete = (data: any, url: string) => {
    setInferenceData(data)
    setPlotUrl(url)
    // Automáticamente cambiar al siguiente tab después de un delay más largo
    setTimeout(() => setActiveTab("chart"), 2000)
  }

  // Función para actualizar datos de gráfica
  const handleChartUpdate = (imageSrc: string, showImage: boolean) => {
    setChartData({ imageSrc, showImage })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Zap className="h-8 w-8 text-purple-400" />
            <h1 className="text-4xl font-bold text-white">QuantumTrade AI</h1>
            <Brain className="h-8 w-8 text-blue-400" />
          </div>
          <p className="text-slate-300 text-lg">
            Predicción de mercados financieros con Machine Learning y Estrategias Cuánticas
          </p>
          <div className="flex items-center justify-center gap-2 mt-4">
            <Badge variant="secondary" className="bg-purple-600 text-white">
              <TrendingUp className="h-4 w-4 mr-1" />
              AI Powered
            </Badge>
            <Badge variant="secondary" className="bg-blue-600 text-white">
              <BarChart3 className="h-4 w-4 mr-1" />
              Quantum Strategies
            </Badge>
          </div>
        </div>

        {/* Main Application */}
        <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-white">Panel de Control</CardTitle>
                <CardDescription className="text-slate-300">
                  Configura y ejecuta tus estrategias de trading cuánticas
                </CardDescription>
              </div>

              {/* Botón de Reinicio */}
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="outline"
                    className="border-red-600 text-red-400 hover:bg-red-600 hover:text-white bg-transparent"
                  >
                    <RotateCcw className="h-4 w-4 mr-2" />
                    Reiniciar
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent className="bg-slate-800 border-slate-700">
                  <AlertDialogHeader>
                    <AlertDialogTitle className="text-white flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5 text-red-400" />
                      ¿Reiniciar aplicación?
                    </AlertDialogTitle>
                    <AlertDialogDescription className="text-slate-300">
                      Esta acción eliminará todos los datos actuales incluyendo:
                      <ul className="list-disc list-inside mt-2 space-y-1">
                        <li>Índice seleccionado</li>
                        <li>Configuración de entrenamiento</li>
                        <li>Modelo entrenado</li>
                        <li>Datos de inferencia</li>
                        <li>Gráficas generadas</li>
                      </ul>
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel className="bg-slate-700 text-white border-slate-600 hover:bg-slate-600">
                      Cancelar
                    </AlertDialogCancel>
                    <AlertDialogAction onClick={handleReset} className="bg-red-600 hover:bg-red-700 text-white">
                      Sí, reiniciar
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-4 bg-slate-700">
                <TabsTrigger value="index" className="text-white data-[state=active]:bg-purple-600">
                  1. Índice
                  {selectedIndex && <span className="ml-1 text-xs">✓</span>}
                </TabsTrigger>
                <TabsTrigger
                  value="train"
                  className="text-white data-[state=active]:bg-purple-600"
                  disabled={!selectedIndex}
                >
                  2. Entrenar
                  {isTrained && <span className="ml-1 text-xs">✓</span>}
                </TabsTrigger>
                <TabsTrigger
                  value="inference"
                  className="text-white data-[state=active]:bg-purple-600"
                  disabled={!isTrained}
                >
                  3. Inferencia
                  {plotUrl && <span className="ml-1 text-xs">✓</span>}
                </TabsTrigger>
                <TabsTrigger value="chart" className="text-white data-[state=active]:bg-purple-600" disabled={!plotUrl}>
                  4. Gráfica
                  {chartData.showImage && <span className="ml-1 text-xs">✓</span>}
                </TabsTrigger>
              </TabsList>

              <TabsContent value="index" className="mt-6">
                <IndexSelector
                  selectedIndex={selectedIndex}
                  onIndexSelect={(index) => {
                    setSelectedIndex(index)
                    // Automáticamente cambiar al siguiente tab
                    setTimeout(() => setActiveTab("train"), 500)
                  }}
                />
              </TabsContent>

              <TabsContent value="train" className="mt-6">
                <ModelTrainer
                  selectedIndex={selectedIndex}
                  trainingData={trainingData}
                  onTrainingDataChange={setTrainingData}
                  onTrainingComplete={handleTrainingComplete}
                />
              </TabsContent>

              <TabsContent value="inference" className="mt-6">
                <InferenceEngine
                  selectedIndex={selectedIndex}
                  inferenceConfig={inferenceConfig}
                  onInferenceConfigChange={setInferenceConfig}
                  onInferenceComplete={handleInferenceComplete}
                />
              </TabsContent>

              <TabsContent value="chart" className="mt-6">
                <ChartVisualization
                  plotUrl={plotUrl}
                  inferenceData={inferenceData}
                  chartData={chartData}
                  onChartUpdate={handleChartUpdate}
                />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Progress Indicator */}
        <div className="mt-6">
          <Card className="bg-slate-800/30 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">Progreso del proceso:</span>
                <div className="flex items-center gap-4">
                  <div className={`flex items-center gap-2 ${selectedIndex ? "text-green-400" : "text-slate-500"}`}>
                    <div className={`w-2 h-2 rounded-full ${selectedIndex ? "bg-green-400" : "bg-slate-500"}`} />
                    Índice
                  </div>
                  <div className={`flex items-center gap-2 ${isTrained ? "text-green-400" : "text-slate-500"}`}>
                    <div className={`w-2 h-2 rounded-full ${isTrained ? "bg-green-400" : "bg-slate-500"}`} />
                    Entrenamiento
                  </div>
                  <div className={`flex items-center gap-2 ${plotUrl ? "text-green-400" : "text-slate-500"}`}>
                    <div className={`w-2 h-2 rounded-full ${plotUrl ? "bg-green-400" : "bg-slate-500"}`} />
                    Inferencia
                  </div>
                  <div
                    className={`flex items-center gap-2 ${chartData.showImage ? "text-green-400" : "text-slate-500"}`}
                  >
                    <div className={`w-2 h-2 rounded-full ${chartData.showImage ? "bg-green-400" : "bg-slate-500"}`} />
                    Visualización
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
