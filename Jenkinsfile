
pipeline {
    agent any

    environment {
        AWS_REGION = 'ap-south-2'
        FUNCTION_NAME = 'aa-csv-processing-lambda'

        INPUT_BUCKET = 'aa-lambda-raw-files-2026'
        OUTPUT_BUCKET = 'aa-lambda-processed-files-2026'
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https:/udaykn13811-hub/github.com//AWS-Lambda-Jenkins-CICD.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 --version
                    python3 -m pip install boto3
                    aws --version
                '''
            }
        }

        stage('Unit Testing') {
            steps {
                sh '''
                    python3 -m unittest test_lambda.py -v
                '''
            }
        }

        stage('Package Lambda') {
            steps {
                sh '''
                    rm -f function.zip
                    zip function.zip lambda_function.py

                    ls -lh function.zip
                '''
            }
        }

        stage('Deploy Lambda') {
            steps {
                sh '''
                    aws lambda update-function-code \
                    --function-name $FUNCTION_NAME \
                    --zip-file fileb://function.zip \
                    --region $AWS_REGION

                    aws lambda wait function-updated \
                    --function-name $FUNCTION_NAME \
                    --region $AWS_REGION
                '''
            }
        }

        stage('Integration Testing') {
            steps {
                sh '''
                    cat > sample.csv <<EOF
name,email
John,john@gmail.com
David,david@gmail.com
,invalid@gmail.com
EOF

                    aws s3 cp sample.csv \
                    s3://$INPUT_BUCKET/uploads/sample.csv \
                    --region $AWS_REGION

                    echo "Waiting for Lambda processing..."

                    for i in $(seq 1 12); do
                        if aws s3api head-object \
                        --bucket $OUTPUT_BUCKET \
                        --key processed/uploads/sample.csv \
                        --region $AWS_REGION >/dev/null 2>&1; then

                            echo "SUCCESS: Processed file found"
                            exit 0
                        fi

                        sleep 5
                    done

                    echo "ERROR: Processed file not found"
                    exit 1
                '''
            }
        }
    }

    post {
        success {
            echo 'Lambda CI/CD Deployment Successful!'
        }

        failure {
            echo 'Lambda CI/CD Pipeline Failed!'
        }

        always {
            echo 'Pipeline execution completed.'
        }
    }
}
