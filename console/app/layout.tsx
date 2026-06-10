import type { Metadata } from "next"
import { Newsreader, Instrument_Sans } from "next/font/google"
import { AppHeader } from "@/components/AppHeader"
import { SubBarProvider } from "@/components/SubBarContext"
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
  title: {
    default: "Curation Console — CoThesis",
    template: "%s — CoThesis Curation",
  },
  description: "Human review console for the CoThesis Compendium curation pipeline",
  icons: {
    icon: "/cothesis_icon_lightbg_transparent.svg",
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${newsreader.variable} ${instrumentSans.variable}`}>
      <body className="min-h-screen font-sans antialiased">
        <SubBarProvider>
          <AppHeader />
          <main className="hitl-main">{children}</main>
        </SubBarProvider>
      </body>
    </html>
  )
}
