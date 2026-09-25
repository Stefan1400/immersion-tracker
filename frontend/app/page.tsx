'use client';

import { useState, useEffect } from "react";

function formatImmersionTime(seconds: number) {
    const totalMinutes = Math.floor(seconds / 60);

    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;

    if (hours > 0 && minutes > 0) {
        return (
            <>
                {hours}
                <span className="text-gray-400 text-6xl">hr</span>
                {minutes}
                <span className="text-gray-400 text-6xl">min</span>
            </>
        );
    }

    if (hours > 0) {
        return (
            <>
                {hours}
                <span className="text-gray-400 text-6xl">hr</span>
            </>
        );
    }

    return (
        <>
            {minutes}
            <span className="text-gray-400 text-6xl">min</span>
        </>
    );
}


export default function Home() {
  const [isImmersing, setIsImmersing] = useState(false);
  const [totalImmersionTime, setTotalImmersionTime] = useState(0);

  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8765");

    socket.onopen = () => {
      console.log("Connected to Python!");
    };

    socket.onmessage = (event) => {
      console.log("Python:", event.data);

      const data = JSON.parse(event.data);

      const language = data.language;
      const immersionTime = data.total_immersion_in_seconds;

      if (language === "ja") {
        setIsImmersing(true);
        setTotalImmersionTime(immersionTime);
      } else {
        setIsImmersing(false);
      }
    };

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    return () => {
      socket.close();
    };
  }, []);
  
  return (
    <div className={`${isImmersing ? 'bg-[#F0F0F0] text-[#171717]' : 'bg-[#0b0b0b] text-white'} transition-all duration-300 flex flex-1 w-full h-full flex-col items-center px-4`}>
  <div className="flex-1" />

  <div className="flex flex-col items-center justify-between gap-3">
    <span className="transition-all duration-300 text-sm sm:text-base">Today's Immersion Time</span>
    <h1 className="transition-all duration-300 text-6xl sm:text-7xl md:text-8xl font-semibold">{formatImmersionTime(totalImmersionTime)}</h1>
    
  </div>

  <div className="flex-1" />

  <span className="transition-all duration-300 font-medium text-sm sm:text-base pb-10 sm:pb-14 md:pb-16">
    {isImmersing ? 'Immersing...' : 'Taking a break...'}
  </span>
</div>
  );
}
