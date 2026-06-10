import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-[var(--radius-signature)] text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-[var(--green-primary)] text-white hover:bg-[var(--green-hover)] focus-visible:ring-[var(--green-primary)]",
        destructive:
          "bg-[var(--color-destructive)] text-white hover:bg-[#b91c1c] focus-visible:ring-[var(--color-destructive)]",
        outline:
          "border border-[var(--border-primary)] bg-white hover:bg-[var(--surface-hover)] text-[var(--text-primary)]",
        secondary:
          "bg-[var(--surface-hover)] text-[var(--text-primary)] hover:bg-[var(--border-primary)]",
        ghost: "hover:bg-[var(--surface-hover)] text-[var(--text-primary)]",
        link: "text-[var(--green-primary)] underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-3.5 py-2 text-sm",
        sm: "h-8 rounded-[var(--radius-signature)] px-2.5 text-xs",
        lg: "h-10 rounded-[var(--radius-signature)] px-6",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
