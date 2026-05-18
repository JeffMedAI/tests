import { useState } from 'react';
import { TopBar } from './components/TopBar';
import { LeftSidebar } from './components/LeftSidebar';
import { RequestQueue } from './components/RequestQueue';
import { DetailPanel } from './components/DetailPanel';
import type { Request } from './components/RequestQueue';

export default function App() {
  const [selectedRequest, setSelectedRequest] = useState<Request | null>(null);

  return (
    <div className="h-screen bg-gray-50 flex flex-col max-w-[1440px] mx-auto overflow-hidden">
      <TopBar />

      <div className="flex flex-1 overflow-hidden">
        <LeftSidebar />
        <div className="flex-1 flex overflow-hidden">
          <RequestQueue
            onSelectRequest={setSelectedRequest}
            selectedRequestId={selectedRequest?.id || null}
          />
          <DetailPanel
            request={selectedRequest}
            onClose={() => setSelectedRequest(null)}
          />
        </div>
      </div>
    </div>
  );
}
