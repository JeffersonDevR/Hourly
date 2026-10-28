import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Botón shadcn/ui con las variantes mapeadas a los tokens de `design/stitch/`.
 * El foco visible es obligatorio (tokens.css); nunca se usa `outline: none` sin reemplazo.
 */
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-sm text-label transition-colors disabled:pointer-events-none disabled:opacity-50 [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-mh-accent text-mh-on-accent hover:bg-mh-accent-deep",
        outline: "border border-mh-border-control text-mh-text hover:bg-mh-raised",
        ghost: "text-mh-secondary hover:bg-mh-raised hover:text-mh-text",
      },
      size: {
        default: "h-12 px-6",
        sm: "h-10 px-4",
        icon: "size-11",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export type ButtonProps = React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  };

export function Button({ className, variant, size, asChild = false, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button";

  return <Comp className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}

export { buttonVariants };
