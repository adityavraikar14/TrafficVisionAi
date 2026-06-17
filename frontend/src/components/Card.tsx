import type { ReactNode } from "react";
import { motion } from "framer-motion";

interface Props {
  title?: string;
  badge?: string;
  children: ReactNode;
  className?: string;
}

export default function Card({ title, badge, children, className = "" }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className={`tv-card p-4 ${className}`}
    >
      {title && (
        <>
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-[15px] font-black text-white m-0">{title}</h3>
            {badge && <span className="tv-chip tv-chip--yellow">{badge}</span>}
          </div>
          <div className="tv-divider" />
        </>
      )}
      {children}
    </motion.div>
  );
}
