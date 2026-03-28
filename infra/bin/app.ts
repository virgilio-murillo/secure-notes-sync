#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { ConfigSyncStack } from '../lib/stack';

const app = new cdk.App();
new ConfigSyncStack(app, 'ConfigSyncStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});
