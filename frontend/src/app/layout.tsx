import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI-NIDS Sentinel | Explainable Network Intrusion Detection",
  description: "Real-Time Host Intrusion Detection with TreeSHAP Explainable Machine Learning",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full antialiased">
      <body className="min-h-full flex flex-col bg-[#070a12] text-slate-100 font-sans">
        {children}
      </body>
    </html>
  );
}
