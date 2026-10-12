"use client";

import { useEffect, useState } from "react";

type Props = {
  endsAt: string | null | undefined;
  secondsLeft?: number | null;
  isFinished?: boolean;
  className?: string;
};

function split(total: number) {
  const s = Math.max(0, total);
  const days = Math.floor(s / 86400);
  const hours = Math.floor((s % 86400) / 3600);
  const mins = Math.floor((s % 3600) / 60);
  const secs = s % 60;
  return { days, hours, mins, secs };
}

export function Countdown({ endsAt, secondsLeft, isFinished, className = "" }: Props) {
  const [left, setLeft] = useState<number | null>(
    typeof secondsLeft === "number" ? secondsLeft : null
  );
  const [finished, setFinished] = useState(!!isFinished);

  useEffect(() => {
    if (!endsAt) {
      setLeft(null);
      setFinished(false);
      return;
    }
    const target = new Date(endsAt).getTime();
    const tick = () => {
      const diff = Math.floor((target - Date.now()) / 1000);
      if (diff <= 0) {
        setLeft(0);
        setFinished(true);
      } else {
        setLeft(diff);
        setFinished(false);
      }
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [endsAt]);

  if (!endsAt) return null;

  if (finished || left === 0) {
    return (
      <div className={`countdown finished ${className}`.trim()}>
        <div>
          <div className="countdown-label">Статус</div>
          <div className="countdown-value">Мероприятие завершено</div>
        </div>
      </div>
    );
  }

  if (left === null) return null;
  const { days, hours, mins, secs } = split(left);

  return (
    <div className={`countdown ${className}`.trim()}>
      <div>
        <div className="countdown-label">До окончания</div>
      </div>
      <div className="countdown-units">
        <div className="countdown-unit">
          <strong>{String(days).padStart(2, "0")}</strong>
          <span>дн</span>
        </div>
        <div className="countdown-unit">
          <strong>{String(hours).padStart(2, "0")}</strong>
          <span>час</span>
        </div>
        <div className="countdown-unit">
          <strong>{String(mins).padStart(2, "0")}</strong>
          <span>мин</span>
        </div>
        <div className="countdown-unit">
          <strong>{String(secs).padStart(2, "0")}</strong>
          <span>сек</span>
        </div>
      </div>
    </div>
  );
}
