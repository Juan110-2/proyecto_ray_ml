"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Loader2, Zap, Calendar, Target } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import axios from "axios"

interface InferenceEngineProps {
  selectedIndex: string
  inferenceConfig: {
    ticker: string
    startDateIn: string
    endDateIn: string
  }
  onInferenceConfigChange: (config: { ticker: string; startDateIn: string; endDateIn: string }) => void
  onInferenceComplete: (data: any, plotUrl: string) => void
}

const tickersByIndex: Record<string, string[]> = {
  downjones: [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "BRK-B",
    "JPM",
    "JNJ",
    "V",
    "PG",
    "MA",
    "UNH",
    "DIS",
    "HD",
    "VZ",
    "NVDA",
    "PYPL",
    "BAC",
    "ADBE",
    "CMCSA",
    "NFLX",
    "NKE",
    "KO",
    "PEP",
    "MRK",
    "PFE",
    "XOM",
    "CVX",
    "WMT",
    "T",
  ],
  "s&p500": [
    "MMM",
    "AOS",
    "ABT",
    "ABBV",
    "ACN",
    "ATVI",
    "ADM",
    "ADBE",
    "ADP",
    "AAP",
    "AAPL",
    "AMAT",
    "APTV",
    "AMD",
    "ARE",
    "ARNC",
    "AOS",
    "APA",
    "AIV",
    "AAPL",
  ],
  nasdaq100: [
    "AAPL",
    "ADBE",
    "ADI",
    "ADP",
    "ADSK",
    "ALGN",
    "AMAT",
    "AMD",
    "AMGN",
    "AMZN",
    "ANSS",
    "ASML",
    "TEAM",
    "ATVI",
    "AZN",
    "BIIB",
    "BKNG",
    "BMRN",
    "CDNS",
    "CERN",
  ],
  tsxcomposite: [
    "AC",
    "ACO-X",
    "ADEN",
    "AFN",
    "AGI",
    "AIF",
    "ALA",
    "AP.UN",
    "ARE",
    "ARX",
    "ATD",
    "BAM",
    "BBD-B",
    "BCE",
    "BHC",
    "BIP.UN",
    "BMO",
    "BNS",
    "BPY.UN",
    "CAE",
  ],
  ftse100: [
    "ADM",
    "AHT",
    "ANTO",
    "AUTO",
    "AV.",
    "AZN",
    "BA.",
    "BARC",
    "BATS",
    "BDEV",
    "BKG",
    "BP.",
    "BRBY",
    "BT-A",
    "CCL",
    "CNA",
    "CPG",
    "CRDA",
    "DCC",
    "DGE",
  ],
  twitter: ["TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "NFLX", "TWTR", "SNAP"],
}

export default function InferenceEngine({
  selectedIndex,
  inferenceConfig,
  onInferenceConfigChange,
  onInferenceComplete,
}: InferenceEngineProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [loadingState, setLoadingState] = useState("")
  const [availableTickers, setAvailableTickers] = useState<string[]>([])

  // Función para actualizar configuración
  const updateInferenceConfig = (field: string, value: string) => {
    onInferenceConfigChange({
      ...inferenceConfig,
      [field]: value,
    })
  }

  useEffect(() => {
    if (selectedIndex && tickersByIndex[selectedIndex]) {
      setAvailableTickers(tickersByIndex[selectedIndex])
    }
  }, [selectedIndex])

  const handleInference = async () => {
    if (!inferenceConfig.ticker || !inferenceConfig.startDateIn || !inferenceConfig.endDateIn) {
      alert("Por favor completa todos los campos")
      return
    }

    setIsLoading(true)
    setLoadingState("Haciendo la inferencia...")

    const InferenceData = {
      ticker: inferenceConfig.ticker,
      start_date: inferenceConfig.startDateIn,
      end_date: inferenceConfig.endDateIn,
      index: selectedIndex,
    }

    try {
      console.log(InferenceData)
      setLoadingState("Procesando datos del mercado...")

      const response = await axios.post("/inference", InferenceData)
      console.log("Respuesta Inferencia", response.data)
      console.log("Respuesta Inferencia", response.data.path)

      setLoadingState("Generando predicciones...")
      onInferenceComplete(response.data, response.data.path)
      setLoadingState("¡Inferencia completada!")
    } catch (error) {
      console.log("Error al hacer la inferencia", error)
      setLoadingState("Error en la inferencia")
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
          <Zap className="h-5 w-5 text-yellow-400" />
          Motor de Inferencia Cuántica
        </CardTitle>
        <CardDescription className="text-slate-300">
          Selecciona el ticker y período para generar predicciones
        </CardDescription>
        <Badge className="bg-yellow-600 text-white w-fit">Índice: {getIndexName()}</Badge>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="ticker" className="text-white flex items-center gap-2">
            <Target className="h-4 w-4" />
            Ticker / Símbolo
          </Label>
          <Select value={inferenceConfig.ticker} onValueChange={(value) => updateInferenceConfig("ticker", value)}>
            <SelectTrigger className="bg-slate-600 border-slate-500 text-white">
              <SelectValue placeholder="Selecciona un ticker..." />
            </SelectTrigger>
            <SelectContent className="bg-slate-600 border-slate-500">
              {availableTickers.map((tickerOption) => (
                <SelectItem key={tickerOption} value={tickerOption} className="text-white hover:bg-slate-500">
                  {tickerOption}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="start-date-in" className="text-white flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Fecha Inicio Inferencia
            </Label>
            <Input
              id="start-date-in"
              type="date"
              value={inferenceConfig.startDateIn}
              onChange={(e) => updateInferenceConfig("startDateIn", e.target.value)}
              className="bg-slate-600 border-slate-500 text-white"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="end-date-in" className="text-white flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Fecha Fin Inferencia
            </Label>
            <Input
              id="end-date-in"
              type="date"
              value={inferenceConfig.endDateIn}
              onChange={(e) => updateInferenceConfig("endDateIn", e.target.value)}
              className="bg-slate-600 border-slate-500 text-white"
            />
          </div>
        </div>

        {isLoading && (
          <div className="p-4 bg-yellow-900/20 border border-yellow-700 rounded-lg">
            <div className="flex items-center gap-3">
              <Loader2 className="h-5 w-5 animate-spin text-yellow-400" />
              <span className="text-yellow-400">{loadingState}</span>
            </div>
          </div>
        )}

        <Button
          onClick={handleInference}
          disabled={isLoading || !inferenceConfig.ticker || !inferenceConfig.startDateIn || !inferenceConfig.endDateIn}
          className="w-full bg-yellow-600 hover:bg-yellow-700 text-white"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Procesando Inferencia...
            </>
          ) : (
            <>
              <Zap className="mr-2 h-4 w-4" />
              Ejecutar Inferencia
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
