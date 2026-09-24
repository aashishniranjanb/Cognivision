import { useEffect, useState } from "react";

export default function AnimatedCounter({ value, duration = 600, prefix = "", suffix = "" }) {
    const [displayVal, setDisplayVal] = useState(value);

    useEffect(() => {
        let startVal = displayVal;
        let endVal = Number(value) || 0;
        if (startVal === endVal) return;

        let startTime = performance.now();

        const updateCounter = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1.0);
            // Ease-out cubic
            const ease = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(startVal + (endVal - startVal) * ease);
            setDisplayVal(current);

            if (progress < 1.0) {
                requestAnimationFrame(updateCounter);
            } else {
                setDisplayVal(endVal);
            }
        };

        const animId = requestAnimationFrame(updateCounter);
        return () => cancelAnimationFrame(animId);
    }, [value, duration]);

    return (
        <span>
            {prefix}{displayVal.toLocaleString()}{suffix}
        </span>
    );
}
