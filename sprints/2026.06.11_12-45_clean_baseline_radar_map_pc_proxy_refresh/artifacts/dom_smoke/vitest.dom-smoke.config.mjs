import vue from '/Users/m1/apps/rober/pc-tools/workstation/node_modules/@vitejs/plugin-vue/dist/index.mjs';

export default {
  plugins: [vue()],
  resolve: {
    alias: {
      vue: '/Users/m1/apps/rober/pc-tools/workstation/node_modules/vue/dist/vue.runtime.esm-bundler.js',
      '@vue/test-utils': '/Users/m1/apps/rober/pc-tools/workstation/node_modules/@vue/test-utils/dist/vue-test-utils.esm-bundler.mjs',
    },
  },
  test: {
    environment: 'jsdom',
  },
};
