"use client";
import { useEffect, useRef } from "react";

export default function TranscriptPanel({ transcript, agentActions }: any) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcript]);

  return (
    <div className="grid grid-cols-3 gap-4 fade-in" style={{ height: "calc(100vh - 180px)" }}>
      {/* Transcript */}
      <div className="col-span-2 card flex flex-col" style={{ height: "100%" }}>
        <h3 className="font-semibold text-gray-900 mb-3">Live Transcript</h3>
        <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-3">
          {transcript.length === 0 ? (
            <div className="text-center text-gray-400 py-12">
              <svg className="mx-auto mb-3" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              </svg>
              <p>Start a voice call to see the live transcript</p>
            </div>
          ) : (
            transcript.map((msg: any, i: number) => (
              <div key={i} className={`flex gap-3 fade-in ${msg.role === "agent" ? "" : "flex-row-reverse"}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                  msg.role === "agent" ? "bg-blue-100 text-blue-700" : "bg-green-100 text-green-700"
                }`}>
                  {msg.role === "agent" ? "AI" : "C"}
                </div>
                <div className={`max-w-[75%] p-3 rounded-2xl text-sm ${
                  msg.role === "agent"
                    ? "bg-white border rounded-tl-sm"
                    : "bg-blue-600 text-white rounded-tr-sm"
                }`}>
                  {msg.text}
                  <div className={`text-xs mt-1 ${msg.role === "agent" ? "text-gray-400" : "text-blue-200"}`}>
                    {msg.time}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Agent Actions sidebar */}
      <div className="card flex flex-col" style={{ height: "100%" }}>
        <h3 className="font-semibold text-gray-900 mb-3">Agent Actions</h3>
        <div className="flex-1 overflow-y-auto space-y-2">
          {agentActions.length === 0 ? (
            <p className="text-sm text-gray-400">No actions yet</p>
          ) : (
            agentActions.map((action: string, i: number) => (
              <div key={i} className="flex items-start gap-2 fade-in">
                <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
                <div className="text-xs font-mono text-gray-600 break-all">{action}</div>
              </div>
            ))
          )}
        </div>

        {/* Quick stats */}
        <div className="border-t pt-3 mt-3">
          <div className="grid grid-cols-2 gap-2 text-center">
            <div>
              <div className="text-xs text-gray-500">Messages</div>
              <div className="text-lg font-bold">{transcript.length}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Tools Used</div>
              <div className="text-lg font-bold">{agentActions.length}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
