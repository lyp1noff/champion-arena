"use client";

import { useEffect, useState } from "react";
import { useTatamiStore } from "@/store/tatami";
import { readSelectedTatamiId, SELECTED_TATAMI_STORAGE_KEY } from "@/lib/tatami-settings";
import "./tatami-screen.css";

export default function ScreenTatami() {
  const [tatamiId, setTatamiId] = useState<string | null>(() => readSelectedTatamiId());
  const [isHydrated, setIsHydrated] = useState(false);

  const {
    status,
    startTimestamp,
    pausedElapsed,
    durationMs,
    score1,
    score2,
    shido1,
    shido2,
    senshu,
    swap_status,
    currentMatch,
  } = useTatamiStore();
  const [localElapsed, setLocalElapsed] = useState(0);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (!tatamiId) window.location.replace("/admin/setup");
  }, [tatamiId]);

  const [hasPlayedBeep, setHasPlayedBeep] = useState(false);

  useEffect(() => {
    if (status !== "running") {
      setHasPlayedBeep(false);
      return;
    }

    if (Math.floor((durationMs - localElapsed) / 100) === 150 && !hasPlayedBeep) {
      const beep = new Audio("/beep.mp3");
      beep.play().catch(() => {});
      setHasPlayedBeep(true);
    }
  }, [localElapsed, durationMs, status, hasPlayedBeep]);

  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === "tatami-storage") {
        const newState = JSON.parse(e.newValue ?? "{}");
        useTatamiStore.setState(newState.state);
      }
      if (e.key === SELECTED_TATAMI_STORAGE_KEY) {
        setTatamiId(e.newValue);
      }
    };

    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  useEffect(() => {
    const updateScale = () => {
      setScale(Math.min(window.innerWidth / 1920, window.innerHeight / 1080));
    };
    updateScale();
    window.addEventListener("resize", updateScale);
    return () => window.removeEventListener("resize", updateScale);
  }, []);

  // Handle timer updates locally on screen
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;
    if (status === "running" && startTimestamp) {
      interval = setInterval(() => {
        const now = Date.now();
        const elapsed = pausedElapsed + (now - startTimestamp);
        setLocalElapsed(elapsed);
      }, 16);
    } else {
      setLocalElapsed(pausedElapsed);
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [status, startTimestamp, pausedElapsed]);

  const formatPartsArray = (ms: number): string[] => {
    const clamped = Math.max(0, ms);
    const totalSeconds = Math.floor(clamped / 1000);
    const minutes = String(Math.floor(totalSeconds / 60)).padStart(1, "0");
    const seconds = String(totalSeconds % 60).padStart(2, "0");
    const centiseconds = String(Math.floor((clamped % 1000) / 10)).padStart(2, "0");

    return [...minutes, ":", ...seconds, ".", ...centiseconds];
  };

  // Use local elapsed time for display
  const remaining = Math.max(0, durationMs - localElapsed);

  const renderDots = (count: number) => {
    const labels = ["C1", "C2", "C3", "HC", "H"];

    return (
      <div className="tatami-penalties">
        {labels.map((label, i) => {
          const isActive = i < count;

          return (
            <div key={label} className={`tatami-penalty ${isActive ? "is-active" : ""}`}>
              {label}
            </div>
          );
        })}
      </div>
    );
  };

  const getTimerColor = () => {
    if (status === "paused" && remaining > 0) return "is-paused";
    if (remaining <= 15000) return "is-expiring";
    return "";
  };

  const chars = formatPartsArray(remaining);

  if (!tatamiId) return null;

  const leftFighter = swap_status
    ? {
        score: score1,
        shido: shido1,
        senshuActive: senshu === 1,
        athlete: currentMatch?.athlete1,
        colorClass: "is-red",
      }
    : {
        score: score2,
        shido: shido2,
        senshuActive: senshu === 2,
        athlete: currentMatch?.athlete2,
        colorClass: "is-blue",
      };

  const rightFighter = swap_status
    ? {
        score: score2,
        shido: shido2,
        senshuActive: senshu === 2,
        athlete: currentMatch?.athlete2,
        colorClass: "is-blue",
      }
    : {
        score: score1,
        shido: shido1,
        senshuActive: senshu === 1,
        athlete: currentMatch?.athlete1,
        colorClass: "is-red",
      };

  return (
    <div className="tatami-screen">
      <div
        className="tatami-stage"
        style={{
          transform: `translate(-50%, -50%) scale(${scale})`,
        }}
      >
        <div className="tatami-background">
          <div className={`tatami-background__gradient ${swap_status ? "is-swapped" : ""}`} />
        </div>

        <div className="tatami-branding">
          <div className="tatami-branding__club">
            <span className="tatami-branding__label">
              ЦФСН {'"'}ІППОН{'"'}
              <br />
              ВІДДІЛЕННЯ КАРАТЕ
            </span>
            <img
              src="/champ_logo.svg"
              alt="Champion Logo"
              className="tatami-branding__champion-logo"
            />
          </div>
          <img
            src="/champ_ippon.png"
            alt="Champion Ippon Logo"
            width={240}
            height={240}
            className="tatami-branding__ippon-logo"
          />
        </div>

        <div className="tatami-heading tatami-heading--bracket">
          {currentMatch?.bracket_display_name || ""}
        </div>

        <div className="tatami-heading tatami-heading--number">TATAMI {tatamiId}</div>

        {isHydrated && currentMatch && currentMatch?.status !== "finished" && (
          <>
            <div className="tatami-timer">
              <div className={`tatami-timer__value ${getTimerColor()}`}>
                {chars.map((ch, i) => {
                  const isCenti = i >= chars.length - 2;
                  const isSeparator = ch === ":" || ch === ".";
                  return (
                    <span
                      key={i}
                      className={isSeparator ? "tatami-timer__separator" : isCenti ? "tatami-timer__centisecond" : undefined}
                    >
                      {ch}
                    </span>
                  );
                })}
              </div>
            </div>

            <div className="tatami-fighter tatami-fighter--left">
              <div className={`tatami-fighter__score ${leftFighter.colorClass}`}>{leftFighter.score}</div>
              {renderDots(leftFighter.shido)}
            </div>

            <div className="tatami-senshu tatami-senshu--left">
              <div className={`tatami-senshu__indicator ${leftFighter.senshuActive ? "is-active" : ""}`} />
            </div>

            <div className="tatami-athlete tatami-athlete--left">
              <div className="tatami-athlete__name">
                {leftFighter?.athlete
                  ? `${leftFighter.athlete.last_name} ${leftFighter.athlete.first_name}${
                      leftFighter.athlete.coaches_last_name && leftFighter.athlete.coaches_last_name.length > 0
                        ? ` (${leftFighter.athlete.coaches_last_name})`
                        : ""
                    }`
                  : "Left Fighter"}
              </div>
            </div>

            <div className="tatami-fighter tatami-fighter--right">
              <div className={`tatami-fighter__score ${rightFighter.colorClass}`}>
                {rightFighter.score}
              </div>
              {renderDots(rightFighter.shido)}
            </div>

            <div className="tatami-senshu tatami-senshu--right">
              <div className={`tatami-senshu__indicator ${rightFighter.senshuActive ? "is-active" : ""}`} />
            </div>

            <div className="tatami-athlete tatami-athlete--right">
              <div className="tatami-athlete__name">
                {rightFighter?.athlete
                  ? `${rightFighter.athlete.last_name} ${rightFighter.athlete.first_name}${
                      rightFighter.athlete.coaches_last_name && rightFighter.athlete.coaches_last_name.length > 0
                        ? ` (${rightFighter.athlete.coaches_last_name})`
                        : ""
                    }`
                  : "Left Fighter"}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
