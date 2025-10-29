#!/bin/bash
set -e

# Deployment script for Banking Mock Log Server
# Usage: ./deploy.sh [local|aws] [options]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=""
AWS_REGION="us-east-1"
PUBLIC_KEY=""
AUTO_APPROVE=false
SKIP_BUILD=false
VERBOSE=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Banking Mock Log Server Deployment Script

Usage: $0 <environment> [options]

Environments:
    local       Deploy to LocalStack (local development)
    aws         Deploy to AWS EC2 (production)

Options:
    --region <region>        AWS region (default: us-east-1)
    --public-key <file>      SSH public key file (required for AWS deployment)
    --auto-approve           Auto-approve Terraform changes
    --skip-build            Skip Docker image build
    --verbose               Enable verbose output
    --help                  Show this help message

Examples:
    $0 local --auto-approve
    $0 aws --public-key ~/.ssh/id_rsa.pub --region us-west-2
    $0 aws --public-key ~/.ssh/id_rsa.pub --auto-approve --verbose

EOF
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if required commands are available
    local required_commands=("terraform" "docker" "curl")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            print_error "$cmd is not installed or not in PATH"
            exit 1
        fi
    done
    
    # Check if Terraform is initialized
    if [ ! -f "config/terraform.tfstate" ] && [ ! -d "config/.terraform" ]; then
        print_status "Initializing Terraform..."
        cd config
        terraform init
        cd ..
    fi
    
    # Check if config directory exists
    if [ ! -d "config" ]; then
        print_error "config directory not found"
        exit 1
    fi
    
    # Check if mock server directory exists
    if [ ! -d "00-mock-servers" ]; then
        print_error "00-mock-servers directory not found"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to validate environment
validate_environment() {
    if [[ "$ENVIRONMENT" != "local" && "$ENVIRONMENT" != "aws" ]]; then
        print_error "Invalid environment: $ENVIRONMENT"
        print_error "Use 'local' or 'aws'"
        exit 1
    fi
    
    if [[ "$ENVIRONMENT" == "aws" && -z "$PUBLIC_KEY" ]]; then
        print_error "Public key file is required for AWS deployment"
        print_error "Use --public-key <file> option"
        exit 1
    fi
    
    if [[ "$ENVIRONMENT" == "aws" && ! -f "$PUBLIC_KEY" ]]; then
        print_error "Public key file not found: $PUBLIC_KEY"
        exit 1
    fi
}

# Function to setup workspace
setup_workspace() {
    print_status "Setting up Terraform workspace: $ENVIRONMENT"
    
    cd config
    
    # Create workspace if it doesn't exist
    if ! terraform workspace list | grep -q "$ENVIRONMENT"; then
        print_status "Creating new workspace: $ENVIRONMENT"
        terraform workspace new "$ENVIRONMENT"
    fi
    
    # Select workspace
    terraform workspace select "$ENVIRONMENT"
    
    print_success "Workspace $ENVIRONMENT selected"
    cd ..
}

# Function to build Docker image
build_docker_image() {
    if [ "$SKIP_BUILD" = true ]; then
        print_warning "Skipping Docker image build"
        return
    fi
    
    print_status "Building Docker image..."
    
    cd 00-mock-servers
    
    # Build the Docker image
    if [ "$VERBOSE" = true ]; then
        docker build -t banking-mock-server:latest .
    else
        docker build -t banking-mock-server:latest . > /dev/null 2>&1
    fi
    
    print_success "Docker image built successfully"
    cd ..
}

# Function to deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying infrastructure to $ENVIRONMENT..."
    
    cd config
    
    # Prepare Terraform variables
    local tf_vars=""
    tf_vars="$tf_vars -var=aws_region=$AWS_REGION"
    tf_vars="$tf_vars -var=environment=$ENVIRONMENT"
    
    if [[ "$ENVIRONMENT" == "aws" && -n "$PUBLIC_KEY" ]]; then
        tf_vars="$tf_vars -var=public_key=$(cat $PUBLIC_KEY)"
    fi
    
    # Plan and apply
    if [ "$AUTO_APPROVE" = true ]; then
        print_status "Applying Terraform configuration (auto-approve)..."
        if [ "$VERBOSE" = true ]; then
            terraform apply $tf_vars -auto-approve
        else
            terraform apply $tf_vars -auto-approve > /dev/null 2>&1
        fi
    else
        print_status "Planning Terraform configuration..."
        terraform plan $tf_vars
        
        print_status "Waiting for confirmation to apply changes..."
        read -p "Do you want to apply these changes? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            terraform apply $tf_vars
        else
            print_warning "Deployment cancelled"
            exit 0
        fi
    fi
    
    print_success "Infrastructure deployed successfully"
    cd ..
}

# Function to show deployment results
show_results() {
    print_status "Getting deployment results..."
    
    cd config
    
    # Get outputs
    local instance_ip=$(terraform output -raw instance_public_ip 2>/dev/null || echo "N/A")
    local server_url=$(terraform output -raw server_url 2>/dev/null || echo "N/A")
    local health_url=$(terraform output -raw health_check_url 2>/dev/null || echo "N/A")
    local ssh_command=$(terraform output -raw ssh_command 2>/dev/null || echo "N/A")
    
    cd ..
    
    echo
    echo "=================================="
    echo "🚀 DEPLOYMENT COMPLETED"
    echo "=================================="
    echo
    echo "Environment: $ENVIRONMENT"
    echo "Region: $AWS_REGION"
    echo
    echo "Server Information:"
    echo "  Instance IP: $instance_ip"
    echo "  Server URL: $server_url"
    echo "  Health Check: $health_url"
    echo
    echo "API Endpoints:"
    echo "  Status: $server_url/"
    echo "  Control: $server_url/control"
    echo "  Health: $health_url"
    echo
    
    if [[ "$ENVIRONMENT" == "aws" && "$ssh_command" != "N/A" ]]; then
        echo "SSH Access:"
        echo "  Command: $ssh_command"
        echo
    fi
    
    echo "Next Steps:"
    echo "1. Wait 2-3 minutes for the server to fully start"
    echo "2. Check health: curl $health_url"
    echo "3. View logs: Follow the container logs command below"
    echo "4. Start/Stop logs: POST to $server_url/control"
    echo
    
    if [[ "$ENVIRONMENT" == "aws" ]]; then
        echo "View Logs:"
        echo "  $ssh_command 'docker logs -f banking-mock-server-container'"
        echo
        echo "Control Server:"
        echo "  Start logs: curl -X POST $server_url/control -H 'Content-Type: application/json' -d '{\"action\":\"start\"}'"
        echo "  Stop logs: curl -X POST $server_url/control -H 'Content-Type: application/json' -d '{\"action\":\"stop\"}'"
        echo
    fi
}

# Function to test deployment
test_deployment() {
    print_status "Testing deployment..."
    
    cd config
    local health_url=$(terraform output -raw health_check_url 2>/dev/null || echo "")
    cd ..
    
    if [ -n "$health_url" ]; then
        print_status "Waiting for server to start..."
        sleep 30
        
        print_status "Testing health endpoint..."
        if curl -f "$health_url" > /dev/null 2>&1; then
            print_success "Health check passed!"
        else
            print_warning "Health check failed. Server may still be starting..."
        fi
    fi
}

# Function to cleanup on exit
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "Deployment failed"
    fi
}

# Set up cleanup trap
trap cleanup EXIT

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        local|aws)
            ENVIRONMENT="$1"
            shift
            ;;
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --public-key)
            PUBLIC_KEY="$2"
            shift 2
            ;;
        --auto-approve)
            AUTO_APPROVE=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate arguments
if [ -z "$ENVIRONMENT" ]; then
    print_error "Environment is required"
    show_usage
    exit 1
fi

# Main execution flow
main() {
    print_status "Starting Banking Mock Log Server deployment..."
    print_status "Environment: $ENVIRONMENT"
    print_status "Region: $AWS_REGION"
    
    check_prerequisites
    validate_environment
    setup_workspace
    build_docker_image
    deploy_infrastructure
    show_results
    test_deployment
    
    print_success "Deployment completed successfully!"
}

# Run main function
main
