const {
  PHASE_DEVELOPMENT_SERVER,
  PHASE_PRODUCTION_BUILD,
} = require("next/constants");

// This uses phases as outlined here: https://nextjs.org/docs/#custom-configuration
module.exports = (phase) => {
  // when started in development mode `next dev` or `npm run dev` regardless of the value of STAGING environmental variable
  const isDev = phase === PHASE_DEVELOPMENT_SERVER;
  // when `next build` or `npm run build` is used
  const isProd = phase === PHASE_PRODUCTION_BUILD;

  const env = {
    API: (() => {
      if (isDev)
        return "https://asia-southeast2-medicalway-ir.cloudfunctions.net/";
      if (isProd) {
        return "https://asia-southeast2-medicalway-ir.cloudfunctions.net/";
      }
      return "API:not (isDev,isProd)";
    })(),
  };

  // next.config.js object
  return {
    env,
  };
};
