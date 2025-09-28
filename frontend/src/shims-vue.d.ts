declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module '*.scss' {
  const content: { [className: string]: string }
  export default content
}

declare module '*.css' {
  const content: { [className: string]: string }
  export default content
}

declare module '*.png' {
  const src: string
  export default src
}

declare module '*.jpg' {
  const src: string
  export default src
}

declare module '*.jpeg' {
  const src: string
  export default src
}

declare module '*.gif' {
  const src: string
  export default src
}

declare module '*.svg' {
  const src: string
  export default src
}

declare module '*.webp' {
  const src: string
  export default src
}

declare module 'nprogress' {
  interface NProgressOptions {
    minimum?: number
    template?: string
    easing?: string
    speed?: number
    trickle?: boolean
    trickleRate?: number
    trickleSpeed?: number
    showSpinner?: boolean
    barSelector?: string
    spinnerSelector?: string
    parent?: string
  }

  interface NProgress {
    configure(options: NProgressOptions): NProgress
    start(): NProgress
    done(force?: boolean): NProgress
    inc(amount?: number): NProgress
    set(amount: number): NProgress
    isStarted(): boolean
    status: number | null
    remove(): void
  }

  const nprogress: NProgress
  export = nprogress
}

declare module 'dayjs/locale/zh-cn' {
  const locale: any
  export = locale
}

declare module 'element-plus/es/locale/lang/zh-cn' {
  const locale: any
  export default locale
}
