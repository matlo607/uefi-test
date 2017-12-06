#!/usr/bin/env groovy

pipeline {
    agent any

    environment {
        PATH = "${PATH}:/sbin"
    }

    stages {
        stage('Build firmware') {
            steps {
                sh 'mkdir build-dir'
                dir ('build-dir') {
                    sh 'cmake ..'
                    sh 'make'
                }
            }
        }

        stage('Build image disk') {
            steps {
                dir ('build-dir') {
                    sh 'make uefi.img'
                }
            }
        }

        stage('Test') {
            steps {
                dir ('build-dir') {
                    sh 'make run-qemu-nographic-tty'
                }
            }
        }
    }
}
