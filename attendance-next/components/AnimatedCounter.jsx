import { useEffect, useState, useRef } from "react";

export default function AnimatedCounter({ value, duration = 800 }) {
    const [displayVal, setDisplayVal] = useState(value);
    const startValRef = useRef(value);
    const startTimeRef = useRef(null);
    const frameIdRef = useRef(null);

    useEffect(() => {
        const startVal = displayVal;
        const targetVal = Number(value);
        if (startVal === targetVal) return;

        startTimeRef.current = null;
        startValRef.current = startVal;

        const step = (timestamp) => {
            if (!startTimeRef.current) startTimeRef.current = timestamp;
            const progress = Math.min((timestamp - startTimeRef.current) / duration, 1);
            // Cubic ease out: 1 - pow(1 - x, 3)
            const easeProgress = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(startValRef.current + (targetVal - startValRef.current) * easeProgress);

            setDisplayVal(current);

            if (progress < 1) {
                frameIdRef.current = requestAnimationFrame(step);
            }
        };

        frameIdRef.current = requestAnimationFrame(step);

        return () => {
            if (frameIdRef.current) cancelAnimationFrame(frameIdRef.current);
        };
    }, [value, duration]);

    return <span>{displayVal}</span>;
}
