// Entry point IaC: tạo Resource Group rồi deploy toàn bộ tài nguyên Azure ML vào trong đó.
targetScope = 'subscription'

@description('Tên Resource Group sẽ được tạo')
param resourceGroupName string = 'rg-taxi-mlops'

@description('Vùng Azure để triển khai tài nguyên')
param location string = 'southeastasia'

@description('Tiền tố đặt tên cho các tài nguyên (chỉ chữ thường + số, <= 8 ký tự)')
param namePrefix string = 'taximlops'

@description('VM size cho Azure ML compute cluster')
param computeVmSize string = 'Standard_DS3_v2'

@description('Số node tối đa của compute cluster')
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
