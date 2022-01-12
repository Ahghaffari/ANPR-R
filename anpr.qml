import QtQuick 2.13
import QtQuick.Window 2.13
import QtQuick.Controls 2.15
import Qt.labs.animation 1.0
import QtQuick.Controls.Material 2.0
import QtQuick.Layouts 1.11
import Qt3D.Core 2.14
import QtWebSockets 1.1
import QtWebView 1.14
import QtQuick.Controls.Universal 2.0

Window {
    id: mainWindow
    title: qsTr("ANPR - Fard Iran")
    width: 1190
    height: 720
    minimumWidth: 1190
    minimumHeight: 720
    maximumWidth: 1190
    maximumHeight: 720

    color: "#ffffff"
    opacity: 1
    visible: true

    signal startButtonActivated(bool deployment,
                                bool gpu,
                                bool log,
                                bool lines,
                                bool road,
                                string location,
                                string fps,
                                string offset1,
                                string offset2,
                                string offset3,
                                string offset4,
                                string offset5)
    signal startButtonDeactivated()
    signal on_message_received()

    TabBar {
        id: tabBar
        x: 0
        y: 0
        width: 1190
        height: 44

        TabButton {
            id: mainTabButton
            text: qsTr("Main")
            checked: true
            layer.enabled: true
        }

        TabButton {
            id: configTabButton
            text: qsTr("Configuration")
        }

        TabButton {
            id: ocrTabButton
            text: qsTr("OCR")
        }

        TabButton {
            id: trackerTabButton
            text: qsTr("Tracker")
            checked: false
        }
    }

    Image {
        id: cameraView
        x: 313
        y: 172
        width: 868
        height: 540
        clip: false
        source: ""
        fillMode: Image.Stretch

        Connections {
            target: connector
            onFrameChanged: cameraView.source = image
        }


    }

    DelayButton {
        id: startButton
        x: 10
        y: 672
        width: 294
        height: 40
        text: qsTr("Start")
        layer.smooth: true
        layer.samples: 16
        layer.mipmap: false
        delay: 1000

        Connections {
            function onPressed() {
                    if(startButton.text == "Stop"){
                        startButton.text = "Start"
                        mainWindow.startButtonDeactivated()
                    }
                }

            function onActivated() {
                startButton.text = "Stop"
                mainWindow.startButtonActivated(deploymentSwitch.checked,
                                                gpuSwitch.checked,
                                                logSwitch.checked,
                                                linesSwitch.checked,
                                                roadTypeSwitch.checked,
                                                locationTextEdit.text,
                                                fpsTextInput.text,
                                                offset1TextInput.text,
                                                offset2TextInput.text,
                                                offset3TextInput.text,
                                                offset4TextInput.text,
                                                offset5TextInput.text)
            }

        }
    }



    Column {
        id: logoLayout
        x: 11
        y: 48
        width: 289
        height: 118
    }

    ColumnLayout {
        id: leftBoxLayout
        x: 11
        y: 172
        width: 294
        height: 472
        z: 2

        RowLayout {
            id: rowLayout1
            width: 294
            height: 100
            Layout.fillHeight: false
            Layout.fillWidth: false

            Text {
                id: element8
                color: "#000000"
                text: qsTr("Location:")
                font.bold: true
                bottomPadding: 10
                Layout.fillWidth: false
                leftPadding: 10
                font.pixelSize: 16
                padding: 10
            }

            TextInput {
                id: locationTextEdit
                objectName: "locationTextEdit"
                width: 80
                height: 20
                color: "#000000"
                text: qsTr(location)
                selectedTextColor: "#1df870"
                selectionColor: "#32f7ee"
                font.pixelSize: 16
            }

        }

        RowLayout {
            id: rowLayout2
            width: 294
            height: 100
            Layout.fillHeight: true
            Layout.fillWidth: true

            Column {
                id: column
                width: 200
                height: 554
                Layout.fillHeight: false
                Layout.fillWidth: true
                leftPadding: 10
                padding: 5

                Text {
                    id: element2
                    color: "#000000"
                    text: qsTr("Deployment")
                    font.bold: true
                    bottomPadding: 10
                    horizontalAlignment: Text.AlignLeft
                    leftPadding: 0
                    font.pixelSize: 16
                    padding: 2
                }


                Text {
                    id: element3
                    color: "#000000"
                    text: qsTr("Use GPU")
                    bottomPadding: 10
                    font.bold: true
                    topPadding: 11
                    leftPadding: 0
                    font.pixelSize: 16
                    padding: 2
                }

                Text {
                    id: element4
                    color: "#000000"
                    text: qsTr("Show camera stream")
                    bottomPadding: 10
                    font.bold: true
                    topPadding: 11
                    leftPadding: 0
                    font.pixelSize: 16
                    padding: 2
                }

                Text {
                    id: element5
                    color: "#000000"
                    text: qsTr("Show lines")
                    bottomPadding: 10
                    font.bold: true
                    topPadding: 11
                    leftPadding: 0
                    font.pixelSize: 16
                    padding: 2
                }

                Text {
                    id: element6
                    color: "#000000"
                    text: qsTr("Road has 3 lanes")
                    bottomPadding: 10
                    font.bold: true
                    topPadding: 11
                    leftPadding: 0
                    font.pixelSize: 16
                    padding: 2
                }

            }

            Column {
                id: column1
                width: 82
                height: 554
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                Layout.fillHeight: false
                Layout.fillWidth: false
                z: 1

                Switch {
                    id: deploymentSwitch
                    topPadding: 0
                    bottomPadding: 10
                    padding: 10
                    objectName: "deploymentSwitch"
                    enabled: true
                    checkable: true
                    checked: deployment
                }

                Switch {
                    id: gpuSwitch
                    objectName: "gpuSwitch"
                    text: qsTr("")
                    topPadding: 0
                    bottomPadding: 10
                    padding: 10
                    checked: use_gpu
                }

                Switch {
                    id: logSwitch
                    objectName: "logSwitch"
                    text: qsTr("")
                    topPadding: 0
                    bottomPadding: 10
                    padding: 10
                    checked: verbose
                }

                Switch {
                    id: linesSwitch
                    objectName: "linesSwitch"
                    text: qsTr("")
                    topPadding: 0
                    bottomPadding: 10
                    padding: 10
                    checked: show_lines
                }

                Switch {
                    id: roadTypeSwitch
                    objectName: "roadTypeSwitch"
                    text: qsTr("")
                    topPadding: 0
                    bottomPadding: 10
                    padding: 10
                    checked: is3line
                }




            }
        }

        RowLayout {
            id: rowLayout8
            width: 100
            height: 100
            Layout.fillWidth: false
            Layout.fillHeight: false


            Label {
                id: label10
                text: qsTr("Camera frame rate:")
                font.pointSize: 12
                font.bold: true
                topPadding: 0
                padding: 10
                Layout.leftMargin: 0
            }

            TextInput {
                id: fpsTextInput
                objectName: "fpsTextInput"
                width: 80
                height: 20
                text: qsTr(fps)
                bottomPadding: 10
                font.pixelSize: 16
            }

            Label {
                id: label11
                text: qsTr("FPS")
                font.pointSize: 12
                bottomPadding: 10
            }


        }

        RowLayout {
            id: rowLayout3
            width: 100
            height: 100
            Layout.fillHeight: false
            Layout.fillWidth: false

            Label {
                id: label
                text: qsTr("Line 1 speed offset:")
                font.bold: true
                Layout.fillWidth: true
                Layout.fillHeight: true
                leftPadding: 10
                topPadding: 0
                padding: 10
                font.pointSize: 12
            }

            TextInput {
                id: offset1TextInput
                objectName: "offset1TextInput"
                width: 80
                height: 20
                text: qsTr(offset1)
                bottomPadding: 10
                font.pixelSize: 16
            }


        }

        RowLayout {
            id: rowLayout4
            width: 100
            height: 100

            Label {
                id: label1
                text: qsTr("Line 2 speed offset:")
                font.bold: true
                leftPadding: 10
                topPadding: 0
                font.pointSize: 12
                padding: 10
            }

            TextInput {
                id: offset2TextInput
                objectName: "offset2TextInput"
                width: 80
                height: 20
                text: qsTr(offset2)
                bottomPadding: 10
                font.pixelSize: 16
            }


        }

        RowLayout {
            id: rowLayout5
            width: 100
            height: 100

            Label {
                id: label2
                text: qsTr("Line 3 speed offset:")
                font.bold: true
                leftPadding: 10
                topPadding: 0
                padding: 10
                font.pointSize: 12
            }

            TextInput {
                id: offset3TextInput
                objectName: "offset3TextInput"
                width: 80
                height: 20
                text: qsTr(offset3)
                bottomPadding: 10
                font.pixelSize: 16
            }


        }

        RowLayout {
            id: rowLayout6
            width: 100
            height: 100

            Label {
                id: label3
                text: qsTr("Line 4 speed offset:")
                font.bold: true
                leftPadding: 10
                topPadding: 0
                font.pointSize: 12
                padding: 10
            }

            TextInput {
                id: offset4TextInput
                objectName: "offset4TextInput"
                width: 80
                height: 20
                text: qsTr(offset4)
                bottomPadding: 10
                font.pixelSize: 16
            }


        }

        RowLayout {
            id: rowLayout7
            width: 100
            height: 100

            Label {
                id: label4
                text: qsTr("Line 5 speed offset:")
                font.bold: true
                leftPadding: 10
                topPadding: 0
                padding: 10
                font.pointSize: 12
            }

            TextInput {
                id: offset5TextInput
                objectName: "offset5TextInput"
                width: 80
                height: 20
                text: qsTr(offset5)
                bottomPadding: 10
                font.pixelSize: 16
            }


        }







    }

    RowLayout {
        id: rowLayout
        x: 313
        y: 45
        width: 868
        height: 118

        ColumnLayout {
            id: columnLayout
            width: 100
            height: 100
            Layout.topMargin: 5
            Layout.margins: 0

            Text {
                id: element
                color: "#000000"
                text: qsTr("Tracker counter:")
                font.pixelSize: 16
            }

            Text {
                id: element1
                color: "#000000"
                text: qsTr("Tracker process queue:")
                font.pixelSize: 16
            }

            Text {
                id: element14
                color: "#000000"
                text: qsTr("Gain:")
                font.pixelSize: 16
            }

            Text {
                id: element16
                color: "#000000"
                text: qsTr("Shutter:")
                font.pixelSize: 16
            }

            Text {
                id: element20
                color: "#000000"
                text: qsTr("IR:")
                font.pixelSize: 16
            }
        }

        ColumnLayout {
            id: columnLayout1
            width: 100
            height: 100
            Layout.minimumWidth: 200
            Layout.fillHeight: false
            Layout.fillWidth: false
            Layout.margins: 0

            Text {
                id: trackerCounterTextBox
                color: "#000000"
                text: qsTr(trackerCounter)
                font.pixelSize: 16

                Connections {
                    target: connector
                    onCounterChanged: trackerCounterTextBox.text = counter
                }
            }

            Text {
                id: trackerQueueTextBox
                color: "#000000"
                text: qsTr(trackerProcessQueueSize)
                font.pixelSize: 16

                Connections {
                    target: connector
                    onQueueChanged: trackerQueueTextBox.text = queue
                }
            }

            Text {
                id: gainTextBox
                color: "#000000"
                text: qsTr(cameraGain)
                font.pixelSize: 16

                Connections {
                    target: connector
                    onGainChanged: gainTextBox.text = gain
                }
            }

            Text {
                id: shutterTextBox
                color: "#000000"
                text: qsTr(cameraShutter)
                font.pixelSize: 16

                Connections {
                    target: connector
                    onShutterChanged: shutterTextBox.text = shutter
                }
            }

            Text {
                id: irTextBox
                color: "#000000"
                text: "0"
                font.pixelSize: 16

                Connections {
                    target: connector
                    onIrChanged: {
                        irTextBox.text = ir_status
                        if(ir_status == "On") {
                            irTextBox.color = "#1df870"
                        } else {
                            irTextBox.color = "#d60707"
                        }
                    }
                }
            }
        }

        ColumnLayout {
            id: columnLayout2
            width: 100
            height: 100
            Layout.margins: 0

            Text {
                id: element15
                color: "#000000"
                text: qsTr("Time:")
                font.pixelSize: 16
            }

            Text {
                id: element17
                color: "#000000"
                text: qsTr("Licence plate:")
                font.pixelSize: 16
            }

            Text {
                id: element18
                color: "#000000"
                text: qsTr("Lane:")
                font.pixelSize: 16
            }

            Text {
                id: element19
                color: "#000000"
                text: qsTr("Car type:")
                font.pixelSize: 16
            }

            Text {
                id: element21
                color: "#000000"
                text: qsTr("Speed:")
                font.pixelSize: 16
            }
        }

        ColumnLayout {
            id: columnLayout3
            width: 100
            height: 100
            Layout.minimumWidth: 200

            Text {
                id: timeTextBox
                color: "#000000"
                font.pixelSize: 16

                Connections {
                    target: connector
                    onTimeChanged: timeTextBox.text = time
                }
            }

            Text {
                objectName: "plateTextBox"
                id: plateTextBox
                color: "#2248ff"
                text: qsTr(licencePlate)
                font.pixelSize: 16

                Connections {
                    target: connector
                    onPlateChanged: plateTextBox.text = plate
                }
            }

            Text {
                id: laneTextBox
                color: "#000000"
                text: qsTr(carLane)
                font.pixelSize: 16

                Connections {
                    target: connector
                    onLaneChanged: laneTextBox.text = lane
                }
            }

            Text {
                id: carTypeTextBox
                color: "#000000"
                text: qsTr(carType)
                font.pixelSize: 16

                Connections {
                    target: connector
                    onCarChanged: carTypeTextBox.text = car
                }
            }

            Text {
                id: speedTextBox
                color: "#000000"
                text: qsTr(carType)
                Connections {
                    target: connector
                    onSpeedChanged: speedTextBox.text = speed
                }
                font.pixelSize: 16
            }
        }
    }

    Frame {
        id: frame
        x: 313
        y: 172
        width: 868
        height: 540

        Image {
            id: image
            x: -314
            y: -136
            width: 294
            height: 118
            z: 1
            fillMode: Image.PreserveAspectFit
            source: "assets/logo2.png"
        }
    }










}

/*##^##
Designer {
    D{i:0;formeditorZoom:1.5}
}
##^##*/
