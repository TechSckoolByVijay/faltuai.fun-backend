# Setup Azure Container Apps for Backend Deployment
# PowerShell script to create Azure Container Apps infrastructure

Write-Host "🚀 Setting up Azure Container Apps for Backend" -ForegroundColor Green
Write-Host "=" * 55

# Variables
$ResourceGroup = "faltuai-rg"
$Location = "eastus"
$ContainerAppEnv = "faltuai-env"
$ContainerAppName = "faltuai-backend-app"
$AcrName = "faltuaicr"
$ImageName = "faltuai-backend"

Write-Host ""
Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "   Resource Group: $ResourceGroup"
Write-Host "   Location: $Location"
Write-Host "   Container App Environment: $ContainerAppEnv"
Write-Host "   Container App: $ContainerAppName"
Write-Host "   ACR: $AcrName.azurecr.io"

Write-Host ""
Write-Host "🔧 Azure CLI Setup Commands:" -ForegroundColor Cyan
Write-Host "=" * 30

Write-Host ""
Write-Host "1. Login to Azure:" -ForegroundColor White
Write-Host "   az login"

Write-Host ""
Write-Host "2. Create Resource Group:" -ForegroundColor White
Write-Host "   az group create --name $ResourceGroup --location $Location"

Write-Host ""
Write-Host "3. Create Container Apps Environment:" -ForegroundColor White
Write-Host "   az containerapp env create \"
Write-Host "     --name $ContainerAppEnv \"
Write-Host "     --resource-group $ResourceGroup \"
Write-Host "     --location $Location"

Write-Host ""
Write-Host "4. Create Container App:" -ForegroundColor White
Write-Host "   az containerapp create \"
Write-Host "     --name $ContainerAppName \"
Write-Host "     --resource-group $ResourceGroup \"
Write-Host "     --environment $ContainerAppEnv \"
Write-Host "     --image $AcrName.azurecr.io/$ImageName`:latest \"
Write-Host "     --target-port 8000 \"
Write-Host "     --ingress external \"
Write-Host "     --registry-server $AcrName.azurecr.io \"
Write-Host "     --registry-username $AcrName \"
Write-Host "     --registry-password `$(az acr credential show --name $AcrName --query passwords[0].value -o tsv) \"
Write-Host "     --cpu 1.0 \"
Write-Host "     --memory 2.0Gi \"
Write-Host "     --min-replicas 1 \"
Write-Host "     --max-replicas 3"

Write-Host ""
Write-Host "5. Enable Continuous Deployment:" -ForegroundColor White
Write-Host "   az containerapp update \"
Write-Host "     --name $ContainerAppName \"
Write-Host "     --resource-group $ResourceGroup \"
Write-Host "     --image $AcrName.azurecr.io/$ImageName`:latest"

Write-Host ""
Write-Host "🔐 GitHub Secrets Setup:" -ForegroundColor Cyan
Write-Host "=" * 25

Write-Host ""
Write-Host "Create a service principal for GitHub Actions:" -ForegroundColor White
Write-Host "az ad sp create-for-rbac \"
Write-Host "  --name `"faltuai-github-actions`" \"
Write-Host "  --role contributor \"
Write-Host "  --scopes /subscriptions/`$(az account show --query id -o tsv)/resourceGroups/$ResourceGroup \"
Write-Host "  --sdk-auth"

Write-Host ""
Write-Host "Add this output as AZURE_CREDENTIALS secret in GitHub:" -ForegroundColor Yellow
Write-Host "Repository Settings → Secrets and variables → Actions → New repository secret"

Write-Host ""
Write-Host "💡 Best Practices for Always Latest Deployment:" -ForegroundColor Blue
Write-Host "=" * 45

Write-Host ""
Write-Host "✅ Container App Revisions:" -ForegroundColor Green
Write-Host "   - Each deployment creates a new revision"
Write-Host "   - Traffic automatically routes to latest revision"
Write-Host "   - Zero-downtime deployments"

Write-Host ""
Write-Host "✅ Image Tagging Strategy:" -ForegroundColor Green
Write-Host "   - Always use 'latest' tag for main branch"
Write-Host "   - Semantic versioning for releases (v1.0.0)"
Write-Host "   - Commit SHA tags for traceability"

Write-Host ""
Write-Host "✅ Automatic Deployment Triggers:" -ForegroundColor Green
Write-Host "   - Push to main branch → Build → Deploy"
Write-Host "   - Manual workflow dispatch available"
Write-Host "   - Only deploys after successful ACR push"

Write-Host ""
Write-Host "🌐 Access URLs:" -ForegroundColor Blue
Write-Host "After deployment, your app will be available at:"
Write-Host "https://$ContainerAppName.${ContainerAppEnv}.${Location}.azurecontainerapps.io"

Write-Host ""
Write-Host "📚 Next Steps:" -ForegroundColor Magenta
Write-Host "1. Run the Azure CLI commands above"
Write-Host "2. Set up AZURE_CREDENTIALS secret in GitHub"
Write-Host "3. Push code to main branch to trigger deployment"
Write-Host "4. Monitor deployments in Azure Portal"