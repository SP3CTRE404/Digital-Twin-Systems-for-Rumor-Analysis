import type React from "react"
import type { Metadata } from "next"
import { GeistSans } from "geist/font/sans"
import { GeistMono } from "geist/font/mono"
import { Analytics } from "@vercel/analytics/next"
import "./globals.css"
import { Source_Serif_4 as V0_Font_Source_Serif_4 } from "next/font/google"
import { Suspense } from "react"

const sourceSerif = V0_Font_Source_Serif_4({
  weight: ["200", "300", "400", "500", "600", "700", "800", "900"],
  subsets: ["latin"],
  variable: "--font-source-serif",
})

export const metadata: Metadata = {
  title: "Sentinel - Rumor Analysis",
  description: "AI-powered rumor detection and analysis platform",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`font-sans ${GeistSans.variable} ${GeistMono.variable} ${sourceSerif.variable} antialiased`}>
        <Suspense fallback="Loading...">{children}</Suspense>
        <Analytics />
      </body>
    </html>
  )
}
