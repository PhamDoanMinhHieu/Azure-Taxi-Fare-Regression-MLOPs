// IaC entry point: creates the Resource Group, then deploys all Azure ML resources into it.
targetScope = 'subscription'

@description('Name of the Resource Group to create')
param resourceGroupName string = 'rg-taxi-mlops'

@description('Azure region to deploy resources into')
param location string = 'southeastasia'

@description('Naming prefix for resources (lowercase letters + digits only, <= 8 chars)')
param namePrefix string = 'taximlops'

@description('VM size for the Azure ML compute cluster')
param computeVmSize string = 'Standard_DS3_v2'

@description('Maximum node count of the compute cluster')
param computeMaxNodes int = 2

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
}

module resources 'resources.bicep' = {
  name: 'taxi-mlops-resources'
  scope: rg
  params: {
    location: location
    namePrefix: namePrefix
    computeVmSize: computeVmSize
    computeMaxNodes: computeMaxNodes
  }
}

output resourceGroupName string = rg.name
output workspaceName string = resources.outputs.workspaceName
