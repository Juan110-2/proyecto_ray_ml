"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Loader2, Brain, Calendar, Play } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import axios from "axios"

interface ModelTrainerProps {
  selectedIndex: string
  trainingData: {
    startDate: string
    endDate: string
    batchSize: string
  }
  onTrainingDataChange: (data: { startDate: string; endDate: string; batchSize: string }) => void
  onTrainingComplete: (success: boolean) => void
}

export default function ModelTrainer({
  selectedIndex,
  trainingData,
  onTrainingDataChange,
  onTrainingComplete,
}: ModelTrainerProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [loadingState, setLoadingState] = useState("")
  const [trained, setTrained] = useState(false)

  // Actualizar datos cuando cambien los inputs
  const updateTrainingData = (field: string, value: string) => {
    onTrainingDataChange({
      ...trainingData,
      [field]: value,
    })
  }

  const handleTrain = async () => {
    if (!trainingData.startDate || !trainingData.endDate) {
      alert("Por favor selecciona las fechas de entrenamiento")
      return
    }

    setIsLoading(true)
    setLoadingState("Iniciando entrenamiento del modelo...")

    const TrainData = {
      index: selectedIndex,
      start_date: trainingData.startDate,
      end_date: trainingData.endDate,
      batch_size: Number.parseInt(trainingData.batchSize),
    }

    try {
      let response
      setLoadingState("Procesando datos históricos...")

      if (selectedIndex === "twitter") {
        response = await axios.get("/train/twitter", {
          params: TrainData,
        })
      } else {
        response = await axios.post("http://127.0.0.1:8001/train/yahoofinance", TrainData)
      }

      console.log("Respuesta entrenamiento", response.data)
      setTrained(true)
      onTrainingComplete(true)
      setLoadingState("¡Entrenamiento completado exitosamente!")
    } catch (error) {
      console.error("Error en el entrenamiento del modelo:", error)
      setTrained(false)
      onTrainingComplete(false)
      setLoadingState("Error en el entrenamiento")
    } finally {
      setTimeout(() => {
        setIsLoading(false)
        setLoadingState("")
      }, 2000)
    }
  }

  const getIndexName = () => {
    const indices: Record<string, string> = {
      "s&p500": "S&P 500",
      downjones: "Dow Jones",
      nasdaq100: "Nasdaq-100",
      twitter: "Twitter (X)",
      tsxcomposite: "TSX Composite",
      ftse100: "FTSE 100",
    }
    return indices[selectedIndex] || selectedIndex
  }

  return (
    <Card className="bg-slate-700/50 border-slate-600">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Brain className="h-5 w-5 text-blue-400" />
          Entrenamiento del Modelo IA
        </CardTitle>
        <CardDescription className="text-slate-300">
          Configura el período de entrenamiento para el modelo de machine learning
        </CardDescription>
        <Badge className="bg-blue-600 text-white w-fit">Índice: {getIndexName()}</Badge>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="start-date" className="text-white flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Fecha Inicio Entrenamiento
            </Label>
            <Input
              id="start-date"
              type="date"
              value={trainingData.startDate}
              onChange={(e) => updateTrainingData("startDate", e.target.value)}
              className="bg-slate-600 border-slate-500 text-white"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="end-date" className="text-white flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Fecha Fin Entrenamiento
            </Label>
            <Input
              id="end-date"
              type="date"
              value={trainingData.endDate}
              onChange={(e) => updateTrainingData("endDate", e.target.value)}
              className="bg-slate-600 border-slate-500 text-white"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="batch-size" className="text-white">
            Tamaño del Lote (Batch Size)
          </Label>
          <Input
            id="batch-size"
            type="number"
            value={trainingData.batchSize}
            onChange={(e) => updateTrainingData("batchSize", e.target.value)}
            className="bg-slate-600 border-slate-500 text-white"
            min="1"
            max="128"
          />
        </div>

        {isLoading && (
          <div className="p-4 bg-blue-900/20 border border-blue-700 rounded-lg">
            <div className="flex items-center gap-3">
              <Loader2 className="h-5 w-5 animate-spin text-blue-400" />
              <span className="text-blue-400">{loadingState}</span>
            </div>
          </div>
        )}

        {trained && !isLoading && (
          <div className="p-4 bg-green-900/20 border border-green-700 rounded-lg">
            <p className="text-green-400">✅ Modelo entrenado exitosamente. Puedes proceder a la inferencia.</p>
          </div>
        )}

        <Button
          onClick={handleTrain}
          disabled={isLoading || !trainingData.startDate || !trainingData.endDate}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Entrenando Modelo...
            </>
          ) : (
            <>
              <Play className="mr-2 h-4 w-4" />
              Iniciar Entrenamiento
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
