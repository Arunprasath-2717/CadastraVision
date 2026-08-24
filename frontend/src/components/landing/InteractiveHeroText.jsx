import React, { useState, useEffect, useRef } from 'react';

/**
 * Interactive Hero Text Effect (PRD-CM-04 Section 7 & Section 41)
 * Inspired by Shopify Horizon Summer '25 visual direction.
 * Creates an expressive repulsion & distortion effect on cursor hover while keeping text readable.
 * Default color: Soft Pastel Blue #AFC8F3. Hover color: Stronger Blue #5B8DEF.
 * Strictly respects prefers-reduced-motion accessibility rules.
 */
export function InteractiveHeroText({ text = "AI-POWERED CADASTRAL INTELLIGENCE" }) {
  const containerRef = useRef(null);
  const [mousePos, setMousePos] = useState({ x: -1000, y: -1000 });
  const [isReducedMotion, setIsReducedMotion] = useState(false);

  // Check reduced motion preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setIsReducedMotion(mediaQuery.matches);

    const handleChange = (e) => setIsReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Split text into words and letters for precise displacement math
  const words = text.split(" ");

  const handleMouseMove = (e) => {
    if (isReducedMotion || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    setMousePos({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    });
  };

  const handleMouseLeave = () => {
    setMousePos({ x: -1000, y: -1000 });
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="relative select-none py-6 cursor-default"
      aria-label={text}
    >
      <h1 className="text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-extrabold tracking-tight leading-[1.05] text-center font-display">
        {words.map((word, wordIdx) => (
          <span key={wordIdx} className="inline-block whitespace-nowrap mx-2 sm:mx-3">
            {word.split("").map((char, charIdx) => {
              const key = `${wordIdx}-${charIdx}`;
              
              // Default letter style: Soft Pastel Blue #AFC8F3
              let style = {
                color: '#AFC8F3',
                WebkitTextFillColor: '#AFC8F3',
              };

              if (!isReducedMotion && containerRef.current) {
                const letterEl = document.getElementById(`letter-${key}`);
                if (letterEl) {
                  const rect = letterEl.getBoundingClientRect();
                  const containerRect = containerRef.current.getBoundingClientRect();
                  const letterX = rect.left - containerRect.left + rect.width / 2;
                  const letterY = rect.top - containerRect.top + rect.height / 2;

                  const dx = mousePos.x - letterX;
                  const dy = mousePos.y - letterY;
                  const dist = Math.sqrt(dx * dx + dy * dy);
                  const maxRadius = 140;

                  if (dist < maxRadius) {
                    const force = (1 - dist / maxRadius);
                    const pushX = -(dx / dist) * force * 24;
                    const pushY = -(dy / dist) * force * 20;
                    const rotate = (dx / dist) * force * 14;
                    const scale = 1 + force * 0.15;

                    style = {
                      transform: `translate3d(${pushX}px, ${pushY}px, 0) rotate(${rotate}deg) scale(${scale})`,
                      color: '#5B8DEF',
                      WebkitTextFillColor: '#5B8DEF',
                      textShadow: '0 0 20px rgba(91, 141, 239, 0.5)',
                    };
                  }
                }
              }

              return (
                <span
                  key={charIdx}
                  id={`letter-${key}`}
                  style={style}
                  className="hero-title-letter transition-all duration-250 ease-out"
                >
                  {char}
                </span>
              );
            })}
          </span>
        ))}
      </h1>
    </div>
  );
}
