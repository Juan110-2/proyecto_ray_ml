"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, MapPin } from "lucide-react"

interface IndexSelectorProps {
  selectedIndex: string
  onIndexSelect: (index: string) => void
}

const marketIndices = [
  {
    id: "s&p500",
    name: "S&P 500",
    fullName: "Standard & Poor's 500 Index",
    country: "🇺🇸 Estados Unidos",
    description: "Las 500 empresas más grandes de EE.UU.",
    color: "bg-blue-600",
  },
  {
    id: "downjones",
    name: "Dow Jones",
    fullName: "Dow Jones Industrial Average (DJIA)",
    country: "🇺🇸 Estados Unidos",
    description: "30 empresas industriales principales",
    color: "bg-green-600",
  },
  {
    id: "nasdaq100",
    name: "Nasdaq-100",
    fullName: "Nasdaq-100 Index",
    country: "🇺🇸 Estados Unidos",
    description: "100 empresas tecnológicas más grandes",
    color: "bg-purple-600",
  },
  {
    id: "twitter",
    name: "Twitter (X)",
    fullName: "Twitter Social Sentiment Index",
    country: "🌐 Global",
    description: "Análisis de sentimiento social",
    color: "bg-sky-600",
  },
  {
    id: "tsxcomposite",
    name: "TSX Composite",
    fullName: "S&P/TSX Composite Index",
    country: "🇨🇦 Canadá",
    description: "Índice principal de la bolsa canadiense",
    color: "bg-red-600",
  },
  {
    id: "ftse100",
    name: "FTSE 100",
    fullName: "Financial Times Stock Exchange 100",
    country: "🇬🇧 Reino Unido",
    description: "100 empresas más grandes del Reino Unido",
    color: "bg-indigo-600",
  },
]

export default function IndexSelector({ selectedIndex, onIndexSelect }: IndexSelectorProps) {
  const [tempSelected, setTempSelected] = useState(selectedIndex)

  const handleConfirm = () => {
    onIndexSelect(tempSelected)
  }

  return (
    <Card className="bg-slate-700/50 border-slate-600">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-purple-400" />
          Selección de Índice Bursátil
        </CardTitle>
        <CardDescription className="text-slate-300">
          Elige el mercado financiero para entrenar tu modelo de IA
        </CardDescription>
      </CardHeader>
      <CardContent>
        <RadioGroup value={tempSelected} onValueChange={setTempSelected}>
          <div className="grid gap-4">
            {marketIndices.map((index) => (
              <div key={index.id} className="flex items-center space-x-3">
                <RadioGroupItem value={index.id} id={index.id} className="border-slate-400 text-purple-400" />
                <Label htmlFor={index.id} className="flex-1 cursor-pointer">
                  <Card className="bg-slate-600/30 border-slate-500 hover:bg-slate-600/50 transition-colors">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge className={`${index.color} text-white`}>{index.name}</Badge>
                            <span className="text-sm text-slate-300 flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {index.country}
                            </span>
                          </div>
                          <h3 className="text-white font-medium mb-1">{index.fullName}</h3>
                          <p className="text-slate-400 text-sm">{index.description}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </Label>
              </div>
            ))}
          </div>
        </RadioGroup>

        {tempSelected && (
          <div className="mt-6 flex justify-end">
            <Button onClick={handleConfirm} className="bg-purple-600 hover:bg-purple-700 text-white">
              Confirmar Selección
            </Button>
          </div>
        )}

        {selectedIndex && (
          <div className="mt-4 p-4 bg-green-900/20 border border-green-700 rounded-lg">
            <p className="text-green-400 text-sm">
              ✅ Índice seleccionado: <strong>{marketIndices.find((i) => i.id === selectedIndex)?.name}</strong>
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
