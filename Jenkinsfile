
pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        timestamps()
    }

    environment {
        AWS_REGION = 'ap-south-2'

        LAMBDA_FUNCTION_NAME = 'aa-csv-processing-lambda'

        INPUT_BUCKET = 'aa-lambda-raw-files-2026'
        OUTPUT_BUCKET = 'aa-lambda-processed-files-2026'

        PYTHON_VENV = '.venv'
        ZIP_FILE = 'function.zip'
    }

    stages {

        // -----------------------------------------
        // STAGE 1: CHECKOUT SOURCE CODE
        // -----------------------------------------

        stage('Checkout') {
            steps {
                echo 'Checking out source code from GitHub'

                checkout scm

                sh '''
                    echo "Repository checkout successful"
                    ls -la
                '''
            }
        }

        // -----------------------------------------
        // STAGE 2: INSTALL DEPENDENCIES
        // -----------------------------------------

        stage('Install Dependencies') {
            steps {
                sh '''
                    set -e

                    echo "Checking Python installation"

                    python3 --version
                    python3 -m pip --version

                    echo "Creating Python virtual environment"

                    python3 -m venv ${PYTHON_VENV}

                    . ${PYTHON_VENV}/bin/activate

                    python -m pip install --upgrade pip

                    echo "Installing boto3"

                    python -m pip install boto3

                    if [ -f requirements.txt ]; then
                        echo "Installing project requirements"
                        python -m pip install -r requirements.txt
                    fi

                    python -c "import boto3; print('Boto3:', boto3.__version__)"

                    echo "Dependencies installed successfully"
                '''
            }
        }

        // -----------------------------------------
        // STAGE 3: UNIT TESTING
        // -----------------------------------------

        stage('Unit Testing') {
            steps {
                sh '''
                    set -e

                    . ${PYTHON_VENV}/bin/activate

                    echo "Running Lambda unit tests"

                    python -m unittest discover -v

                    echo "Unit testing completed successfully"
                '''
            }
        }

        // -----------------------------------------
        // STAGE 4: PACKAGE LAMBDA
        // -----------------------------------------

        stage('Package Lambda') {
            steps {
                sh '''
                    set -e

                    echo "Preparing Lambda deployment package"

                    test -f lambda_function.py

                    rm -rf package
                    rm -f ${ZIP_FILE}

                    mkdir package

                    cp lambda_function.py package/

                    cd package

                    zip -r ../${ZIP_FILE} .

                    cd ..

                    echo "Lambda package created"

                    ls -lh ${ZIP_FILE}

                    echo "Checking ZIP contents"

                    unzip -l ${ZIP_FILE}
                '''
            }

            post {
                success {
                    archiveArtifacts artifacts: 'function.zip',
                                     fingerprint: true
                }
            }
        }

        // -----------------------------------------
        // STAGE 5: DEPLOY LAMBDA TO AWS
        // -----------------------------------------

        stage('Deploy Lambda') {
            steps {
                sh '''
                    set -e

                    echo "Checking AWS identity"

                    aws sts get-caller-identity \
                        --region ${AWS_REGION}

                    echo "Deploying Lambda function"

                    aws lambda update-function-code \
                        --function-name ${LAMBDA_FUNCTION_NAME} \
                        --zip-file fileb://${ZIP_FILE} \
                        --region ${AWS_REGION}

                    echo "Waiting for Lambda deployment"

                    aws lambda wait function-updated \
                        --function-name ${LAMBDA_FUNCTION_NAME} \
                        --region ${AWS_REGION}

                    echo "Lambda deployment successful"

                    aws lambda get-function-configuration \
                        --function-name ${LAMBDA_FUNCTION_NAME} \
                        --region ${AWS_REGION} \
                        --query '[FunctionName,Runtime,State,LastUpdateStatus]' \
                        --output table
                '''
            }
        }

        // -----------------------------------------
        // STAGE 6: INTEGRATION TESTING
        // -----------------------------------------

        stage('Integration Testing') {
            steps {
                sh '''
                    set -e

                    echo "Creating integration test CSV"

                    TEST_FILE="jenkins-test-${BUILD_NUMBER}.csv"

                    cat > ${TEST_FILE} <<EOF
name,email
John,JOHN@GMAIL.COM
David,david@example.com
,invalid@gmail.com
EOF

                    echo "Uploading CSV to input S3 bucket"

                    aws s3 cp ${TEST_FILE} \
                        s3://${INPUT_BUCKET}/uploads/${TEST_FILE} \
                        --region ${AWS_REGION}

                    echo "Waiting for Lambda to process the file"

                    OUTPUT_KEY="processed/uploads/${TEST_FILE}"

                    FOUND=false

                    for i in $(seq 1 30)
                    do
                        if aws s3api head-object \
                            --bucket ${OUTPUT_BUCKET} \
                            --key "${OUTPUT_KEY}" \
                            --region ${AWS_REGION} >/dev/null 2>&1
                        then
                            FOUND=true
                            break
                        fi

                        echo "Waiting for processed file... attempt ${i}"
                        sleep 5
                    done

                    if [ "$FOUND" != "true" ]; then
                        echo "ERROR: Processed file not found"
                        exit 1
                    fi

                    echo "Processed file found successfully"

                    aws s3 cp \
                        s3://${OUTPUT_BUCKET}/${OUTPUT_KEY} \
                        processed-output.csv \
                        --region ${AWS_REGION}

                    echo "Checking processed CSV content"

                    cat processed-output.csv

                    grep -q "John,john@gmail.com" processed-output.csv

                    grep -q "David,david@example.com" processed-output.csv

                    if grep -q "invalid@gmail.com" processed-output.csv; then
                        echo "ERROR: Invalid record was not filtered"
                        exit 1
                    fi

                    echo "Integration testing successful"
                    echo "Lambda processed the CSV correctly"
                '''
            }
        }
    }

    // -----------------------------------------
    // POST BUILD ACTIONS
    // -----------------------------------------

    post {
        success {
            echo '''
            =========================================
                 AWS LAMBDA CI/CD PIPELINE
            =========================================
                 BUILD STATUS: SUCCESS
                 DEPLOYMENT: COMPLETED
                 INTEGRATION TEST: PASSED
            =========================================
            '''
        }

        failure {
            echo '''
            =========================================
                 AWS LAMBDA CI/CD PIPELINE
            =========================================
                 BUILD STATUS: FAILED
                 Check Console Output for errors.
            =========================================
            '''
        }

        always {
            echo 'Pipeline execution completed'
        }
    }
}
