import Sidebar from "@/components/layout/Sidebar"
import ChatPanel from "@/components/chat/ChatPanel"
import ArtifactPanel from "@/components/artifact/ArtifactPanel"

export default function HomePage() {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-surface-black">
      <Sidebar />
      <ChatPanel />
      <ArtifactPanel />
    </div>
  )
}