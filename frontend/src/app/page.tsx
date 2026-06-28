import Sidebar from "@/components/layout/Sidebar"
import ChatPanel from "@/components/chat/ChatPanel"
import ArtifactPanel from "@/components/artifact/ArtifactPanel"
import ArtifactExportDocument from "@/components/export/ArtifactExportDocument"

export default function HomePage() {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-surface-black">
      <Sidebar />
      <ChatPanel />
      <ArtifactPanel />
      {/* Hidden off-screen, only rendered when printing/exporting to PDF.
          Combines all five artifact tabs into one printable document so
          "PDF (print)" exports just the artifacts, not the whole app. */}
      <ArtifactExportDocument />
    </div>
  )
}