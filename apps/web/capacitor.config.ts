import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'io.github.styayur.calligraphystudio',
  appName: 'Calligraphy Studio',
  webDir: 'dist',
  bundledWebRuntime: false,
  android: {
    backgroundColor: '#f4efe5',
    allowMixedContent: false,
  },
}

export default config
