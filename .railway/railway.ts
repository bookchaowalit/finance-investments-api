import { defineRailway, project, service } from "railway/iac";

// investments: the Investments cell. Variables stay unmanaged (secrets live in Railway only).
// investments-api sleeps when idle (Railway Serverless) and wakes on the next request.
// Every service runs in Singapore next to Neon (aws-ap-southeast-1) and empire-platform; the IaC does not
// carry the region, so after the first deploy: railway scale --service <svc> asia-southeast1-eqsg3a=1 us-east4-eqdc4a=0
export default defineRailway(() => {
  const api = service("investments-api", {
    healthcheck: "/health",
    healthcheckTimeout: 60,
    deploy: { sleepApplication: true },
  });

  return project("investments", {
    variables: { managed: false },
    resources: [api],
  });
});
