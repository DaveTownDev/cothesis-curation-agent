import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2 py-0.5 text-[0.6875rem] font-semibold transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-[var(--green-primary)] text-white",
        secondary: "border-transparent bg-[var(--surface-hover)] text-[var(--text-primary)]",
        teal: "border-transparent bg-[var(--color-teal-accent)] text-white",
        outline: "border-[var(--border-primary)] text-[var(--text-primary)]",
        destructive: "border-transparent bg-[var(--color-destructive)] text-white",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
