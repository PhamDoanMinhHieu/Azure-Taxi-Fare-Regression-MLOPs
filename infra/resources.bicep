// Resources inside the Resource Group: Storage, Key Vault, App Insights, Azure ML Workspace, Compute Cluster
@description('Azure region to deploy resources into')
param location string

@description('Naming prefix for resources')
param namePrefix string

@description('VM size for the Azure ML compute cluster')
param computeVmSize string

@description('Maximum node count of the compute cluster')
param computeMaxNodes int

var uniqueSuffix = uniqueString(resourceGroup().id)
var storageAccountName = toLower('${namePrefix}st${uniqueSuffix}')
var keyVaultName = toLower('${namePrefix}-kv-${uniqueSuffix}')
var appInsightsName = '${namePrefix}-appi-${uniqueSuffix}'
var workspaceName = '${namePrefix}-mlw-${uniqueSuffix}'
var computeClusterName = 'taxi-cpu-cluster'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: []
    enableSoftDelete: true
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
  }
}

resource workspace 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: workspaceName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: 'Taxi Fare MLOps Workspace'
    storageAccount: storageAccount.id
    keyVault: keyVault.id
    applicationInsights: appInsights.id
    publicNetworkAccess: 'Enabled'
  }
}

resource computeCluster 'Microsoft.MachineLearningServices/workspaces/computes@2024-04-01' = {
  parent: workspace
  name: computeClusterName
  location: location
  properties: {
    computeType: 'AmlCompute'
    properties: {
      vmSize: computeVmSize
      vmPriority: 'Dedicated'
      scaleSettings: {
        minNodeCount: 0
        maxNodeCount: computeMaxNodes
        nodeIdleTimeBeforeScaleDown: 'PT15M'
      }
    }
  }
}

output workspaceName string = workspace.name
output computeClusterName string = computeCluster.name
output storageAccountName string = storageAccount.name
