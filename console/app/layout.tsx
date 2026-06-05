import type { Metadata } from "next"
import { Newsreader, Instrument_Sans } from "next/font/google"
import { NavBar } from "@/components/NavBar"
import "./globals.css"

const newsreader = Newsreader({
  subsets: ["latin"],
  variable: "--font-newsreader",
  display: "swap",
})

const instrumentSans = Instrument_Sans({
  subsets: ["latin"],
  variable: "--font-instrument-sans",
  display: "swap",
})

export const metadata: Metadata = {
  title: "CoThesis Curation Console",
  description: "Human review console for the CoThesis Compendium curation pipeline",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${newsreader.variable} ${instrumentSans.variable}`}>
      <body className="min-h-screen bg-[#F8F5EE] font-sans antialiased">
        <header className="border-b border-[#d4cfc5] bg-[#0E3A27]">
          <div className="mx-auto max-w-6xl px-4 py-3 flex items-center gap-3">
            <span className="text-white font-serif text-lg font-semibold tracking-tight">
              CoThesis
            </span>
            <span className="text-[#a8c4b0] text-sm mr-4">Curation Console</span>
            <NavBar />
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-8">{children}</main>
      </body>
    </html>
  )
}
