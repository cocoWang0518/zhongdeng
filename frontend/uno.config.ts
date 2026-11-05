import process from 'node:process'

import {
  defineConfig,
  presetAttributify,
  presetIcons,
  presetWebFonts,
  presetWind4,
} from 'unocss'

const isTest = process.env.VITEST === 'true' || process.env.NODE_ENV === 'test'

export default defineConfig({
  shortcuts: [
    ['btn', 'px-4 py-1 rounded inline-block bg-teal-600 text-white cursor-pointer hover:bg-teal-700 disabled:cursor-default disabled:bg-gray-600 disabled:opacity-50'],
    ['icon-btn', 'text-[0.9em] inline-block cursor-pointer select-none opacity-75 transition duration-200 ease-in-out hover:opacity-100 hover:text-teal-600'],
  ],
  presets: [
    presetWind4(),
    presetAttributify(),
    presetIcons({
      scale: 1.2,
      warn: true,
    }),
    ...(isTest
      ? []
      : [
          presetWebFonts({
            fonts: {
              sans: ['DM Sans', 'Noto Sans Simplified Chinese'],
              serif: 'DM Serif Display',
              mono: 'DM Mono',
            },
          }),
        ]),
  ],
})
