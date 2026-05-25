declare module "*.vue" {
  import type { DefineComponent } from "vue";

  // Vue SFC 由 Vite/Vue 插件编译；这里仅给 TypeScript 提供类型入口。
  const component: DefineComponent<Record<string, unknown>, Record<string, unknown>, unknown>;
  export default component;
}
