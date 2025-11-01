import { useEffect, useRef, useState } from 'react';

export function useCountdown(initialSeconds: number | null, isActive: boolean) {
  const [secondsRemaining, setSecondsRemaining] = useState<number | null>(initialSeconds);
  const intervalRef = useRef<number | null>(null);

  useEffect(() => {
    setSecondsRemaining(initialSeconds);
  }, [initialSeconds]);

  useEffect(() => {
    if (!isActive || secondsRemaining === null) {
      if (intervalRef.current !== null) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return undefined;
    }

    intervalRef.current = window.setInterval(() => {
      setSecondsRemaining((previous) => {
        if (previous === null) {
          return null;
        }
        return Math.max(0, previous - 1);
      });
    }, 1000);

    return () => {
      if (intervalRef.current !== null) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isActive, secondsRemaining]);

  return secondsRemaining;
}
