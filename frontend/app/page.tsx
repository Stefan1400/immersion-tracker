'use client';

import { useState } from "react";

export default function Home() {
  const [isImmersing, setIsImmersing] = useState(false);
  
  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
        <h1 className="text-3xl">{isImmersing ? 'Immersing...' : 'Taking a break...'}</h1>

        <div className="flex flex-col items-center justify-between">
          <span>Today's Immersion Time</span>
          <span>10:00</span>
        </div>
      </main>
    </div>
  );
}
