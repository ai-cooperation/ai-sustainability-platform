import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import LayoutShell from "@/components/LayoutShell";
import { AppProvider } from "@/lib/context";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#10b981",
};

const BASE_URL = "https://cooperation.tw/ai-sustainability-platform";

export const metadata: Metadata = {
  title: "AI 永續發展平台 | AI Sustainability Platform",
  description:
    "即時監測台灣永續發展指標：再生能源、碳排放、空氣品質、水資源、農業數據。AI 驅動的環境數據分析平台。",
  keywords: [
    "永續發展",
    "ESG",
    "再生能源",
    "台灣電力",
    "碳排放",
    "空氣品質",
    "sustainability",
    "Taiwan",
    "renewable energy",
    "carbon emissions",
    "air quality",
  ],
  authors: [{ name: "AI Cooperation" }],
  metadataBase: new URL(BASE_URL),
  alternates: {
    canonical: "/",
  },
  openGraph: {
    type: "website",
    url: BASE_URL,
    siteName: "AI Sustainability Platform",
    title: "AI 永續發展平台 | AI Sustainability Platform",
    description:
      "Real-time monitoring of Taiwan's sustainability indicators: renewable energy, carbon emissions, air quality, water resources, agriculture data.",
    locale: "zh_TW",
    images: [
      {
        url: `${BASE_URL}/og-image.png`,
        width: 1200,
        height: 630,
        alt: "AI Sustainability Platform",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "AI 永續發展平台 | AI Sustainability Platform",
    description:
      "即時監測台灣永續發展指標：再生能源、碳排放、空氣品質、水資源、農業數據。",
    images: [`${BASE_URL}/og-image.png`],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-TW" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased bg-gray-50 dark:bg-gray-950`}>
        <AppProvider>
          <LayoutShell>
            {children}
          </LayoutShell>
        </AppProvider>
      </body>
    </html>
  );
}
