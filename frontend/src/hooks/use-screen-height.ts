"use client";

import { useEffect, useState } from "react";

export function useScreenHeight() {
  const [height, setHeight] = useState(0);

  useEffect(() => {
    const update = () => setHeight(window.innerHeight);
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  return height;
}
