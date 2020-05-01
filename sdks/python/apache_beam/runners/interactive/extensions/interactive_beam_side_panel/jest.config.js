module.exports = {
  "roots": [
    "<rootDir>/src"
  ],
  "testMatch": [
    "<rootDir>/src/__tests__/**/*.test.(ts|tsx)"
  ],
  "transform": {
    "^.+\\.(ts|tsx)$": "ts-jest"
  },
  "moduleNameMapper": {
    "\\.(css|less)$": "identity-obj-proxy"
  }
}
