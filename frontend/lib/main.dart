import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:ui' as ui;
import 'dart:typed_data';
import 'package:flutter/rendering.dart';
import 'dart:html' as html;
import 'package:house_plan_app/splash_page.dart';
import 'dart:math' as math;

void main() => runApp(MyApp());

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Smart 2D House Plan Generator',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: SplashPage(),
    );
  }
}

class HousePlanGenerator extends StatefulWidget {
  @override
  _HousePlanGeneratorState createState() => _HousePlanGeneratorState();
}

class _HousePlanGeneratorState extends State<HousePlanGenerator> {
  String selectedLifestyle = 'Work-from-home';
  int selectedPlanIndex = 0;
  GlobalKey canvasKey = GlobalKey();
  List<Map<String, dynamic>> generatedPlans = [];
  bool isGenerating = false;
  List<Map<String, dynamic>> roomGaps = [];
  Map<String, dynamic> validation = {};

  Map<String, List<String>> lifestyleRooms = {
    'Work-from-home': [
      'Master Bedroom',
      'Bedroom',
      'Office',
      'Kitchen',
      'Living Room',
      'Family Room',
      'Storage Room',
      'Utility Room',
      'Bathroom',
    ],
    'Family with kids': [
      'Master Bedroom',
      'Bedroom',
      'Living Room',
      'Dining Room',
      'Kids Room',
      'Kitchen',
      'Bathroom',
      'Family Room',
    ],
    'Elderly-friendly': [
      'Master Bedroom',
      'Living Room',
      'Dining Room',
      'Kitchen',
      'Guest Room',
      'Guest Bathroom',
      'Elderly Bathroom',
      'Bathroom',
      'Utility Room',
    ],
    'Pet owner': [
      'Living Room',
      'Pet Room',
      'Kitchen',
      'Bedroom',
      'Bathroom',
      'Family Room',
    ],
    'Minimalist': [
      'Master Bedroom',
      'Bedroom',
      'Living Room',
      'Kitchen',
      'Bathroom',
    ],
    'Entertainer lifestyle': [
      'Living Room',
      'Bedroom',
      'Kitchen',
      'Dining Room',
      'Family Room',
      'Guest Room',
      'Guest Bathroom',
      'Bathroom',
    ],
    'Remote worker': [
      'Office',
      'Master Bedroom',
      'Bedroom',
      'Living Room',
      'Dining Room',
      'Kitchen',
      'Bathroom',
    ],
    'Eco-friendly': [
      'Master Bedroom',
      'Bedroom',
      'Living Room',
      'Kitchen',
      'Bathroom',
      'Utility Room',
      'Family Room',
    ],
    'Hobbyist': [
      'Workshop',
      'Living Room',
      'Kitchen',
      'Bedroom',
      'Utility Room',
      'Bathroom',
    ],
    'Fitness Enthusiast': [
      'Gym',
      'Bedroom',
      'Living Room',
      'Kitchen',
      'Bathroom',
    ],
    'Multigenerational family': [
      'Master Bedroom',
      'Bedroom',
      'Living Room',
      'Kitchen',
      'Family Room',
      'Guest Room',
      'Guest Bathroom',
      'Bathroom',
    ],
    'Smart Home Lover': [
      'Living Room',
      'Office',
      'Kitchen',
      'Bathroom',
      'Bedroom',
    ],
    'Social Butterfly': [
      'Living Room',
      'Dining Room',
      'Kitchen',
      'Family Room',
      'Bedroom',
      'Guest Room',
      'Guest Bathroom',
      'Bathroom',
    ],
    'Accessibility Focused': [
      'Master Bedroom',
      'Bedroom',
      'Living Room',
      'Kitchen',
      'Guest Room',
      'Guest Bathroom',
      'Bathroom',
      'Utility Room',
    ],
  };

  Map<String, Map<String, TextEditingController>> roomControllers = {};

  @override
  void initState() {
    super.initState();
    initializeRoomControllers();
  }

  @override
  void dispose() {
    roomControllers.forEach((room, map) {
      map.forEach((key, controller) => controller.dispose());
    });
    roomControllers.clear();
    super.dispose();
  }

  void initializeRoomControllers() {
    roomControllers.forEach((room, map) {
      map.forEach((key, controller) => controller.dispose());
    });
    roomControllers = {};

    List<String> rooms = lifestyleRooms[selectedLifestyle] ?? [];
    for (var room in rooms) {
      roomControllers[room] = {
        'count': TextEditingController(text: ''),
        'length': TextEditingController(text: ''),
        'width': TextEditingController(text: ''),
      };
    }
  }

  Future<void> addRoomDataToBackend() async {
    try {
      Map<String, dynamic> payload = {
        'lifestyle': selectedLifestyle,
        'rooms': {},
      };
      for (var room in lifestyleRooms[selectedLifestyle]!) {
        int? count = int.tryParse(roomControllers[room]!['count']!.text) ?? 1;
        double? length = double.tryParse(
          roomControllers[room]!['length']!.text,
        );
        double? width = double.tryParse(roomControllers[room]!['width']!.text);

        if ((roomControllers[room]!['length']!.text.isNotEmpty &&
                length == null) ||
            (roomControllers[room]!['width']!.text.isNotEmpty &&
                width == null)) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                "Invalid input for $room. Please enter numbers only.",
              ),
            ),
          );
          return;
        }

        payload['rooms'][room] = {
          'count': count,
          'length': length ?? 0.0,
          'width': width ?? 0.0,
        };
      }

      print("Payload to backend: ${jsonEncode(payload)}");
      var response = await http
          .post(
            Uri.parse('http://127.0.0.1:5000/add_room_data'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(payload),
          )
          .timeout(
            Duration(seconds: 300),
            onTimeout: () {
              return http.Response('Request timed out', 408);
            },
          );
      print("Backend response: ${response.body}");

      if (response.statusCode == 200) {
        showDialog(
          context: context,
          builder: (_) => AlertDialog(
            title: Text('Success'),
            content: Text('Data received successfully!'),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text('OK'),
              ),
            ],
          ),
        );
      } else {
        throw Exception('Failed to send data: ${response.statusCode}');
      }
    } catch (e) {
      print("Error adding room data: $e");
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: Text('Error'),
          content: Text(
            'Could not send data to backend. Check console for details.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text('OK'),
            ),
          ],
        ),
      );
    }
  }

  Future<void> generatePlansFromBackend() async {
    if (isGenerating) return;

    setState(() => isGenerating = true);

    try {
      Map<String, dynamic> payload = {
        'lifestyle': selectedLifestyle,
        'rooms': {},
      };

      for (var room in lifestyleRooms[selectedLifestyle]!) {
        int? count = int.tryParse(roomControllers[room]!['count']!.text) ?? 1;
        double? length = double.tryParse(
          roomControllers[room]!['length']!.text,
        );
        double? width = double.tryParse(roomControllers[room]!['width']!.text);

        if ((roomControllers[room]!['length']!.text.isNotEmpty &&
                length == null) ||
            (roomControllers[room]!['width']!.text.isNotEmpty &&
                width == null)) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                "Invalid input for $room. Please enter numbers only.",
              ),
            ),
          );
          setState(() => isGenerating = false);
          return;
        }

        payload['rooms'][room] = {
          'count': count,
          'length': length ?? 0.0,
          'width': width ?? 0.0,
        };
      }

      print("Payload to backend for generating plans: ${jsonEncode(payload)}");

      var response = await http
          .post(
            Uri.parse('http://127.0.0.1:5000/generate_plan'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(payload),
          )
          .timeout(
            Duration(seconds: 300),
            onTimeout: () {
              print('Request timed out at ${DateTime.now()}');
              return http.Response('Timeout', 408);
            },
          );

      print("Backend raw response: ${response.body}");

      if (response.statusCode == 200) {
        try {
          var data = jsonDecode(response.body);
          List<Map<String, dynamic>> plans = (data['plans'] as List)
              .map((plan) => Map<String, dynamic>.from(plan))
              .toList();
          setState(() {
            generatedPlans = plans;
            selectedPlanIndex = 0;
            if (plans.isNotEmpty) {
              roomGaps = List<Map<String, dynamic>>.from(
                plans[0]['room_gaps'] ?? [],
              );
              validation = Map<String, dynamic>.from(
                plans[0]['validation'] ?? {},
              );
            } else {
              roomGaps = [];
              validation = {};
            }
          });

          showDialog(
            context: context,
            builder: (_) => AlertDialog(
              title: Text('Success'),
              content: Text('Plans Generated!'),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: Text('OK'),
                ),
              ],
            ),
          );
        } catch (e) {
          print("JSON Decoding Error: $e");
          showDialog(
            context: context,
            builder: (_) => AlertDialog(
              title: Text('Error'),
              content: Text('Invalid response format or JSON error: $e'),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: Text('OK'),
                ),
              ],
            ),
          );
        }
      } else {
        throw Exception('Failed to generate plans: ${response.statusCode}');
      }
    } catch (e) {
      print("General Error: $e");
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: Text('Error'),
          content: Text('Could not generate plans from backend: $e'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text('OK'),
            ),
          ],
        ),
      );
    } finally {
      setState(() => isGenerating = false);
    }
  }

  Future<void> captureAndSaveCanvas() async {
    try {
      if (canvasKey.currentContext == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Canvas not ready. Please generate a plan first.'),
          ),
        );
        return;
      }

      RenderRepaintBoundary boundary =
          canvasKey.currentContext!.findRenderObject() as RenderRepaintBoundary;
      ui.Image image = await boundary.toImage(pixelRatio: 1.5);
      ByteData? byteData = await image.toByteData(
        format: ui.ImageByteFormat.png,
      );
      Uint8List pngBytes = byteData!.buffer.asUint8List();

      if (identical(0, 0.0)) {
        final blob = html.Blob([pngBytes]);
        final url = html.Url.createObjectUrlFromBlob(blob);
        final anchor = html.AnchorElement(href: url)
          ..setAttribute("download", "house_plan.png")
          ..click();
        html.Url.revokeObjectUrl(url);
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Plan downloaded!')));
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Download is only supported in web mode in this version.',
            ),
          ),
        );
      }
    } catch (e) {
      print("Capture/Save Error: $e");
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Error saving plan: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    Map<String, dynamic> selectedPlan = generatedPlans.isNotEmpty
        ? generatedPlans[selectedPlanIndex]
        : {};
    List<dynamic> selectedPlanRooms = selectedPlan['rooms'] ?? [];
    // Check if plan has a main entrance
    bool hasMainEntrance = selectedPlanRooms.any(
      (room) => room['is_entrance'] == true || room['room'] == 'Main Entrance',
    );

    if (!hasMainEntrance && generatedPlans.isNotEmpty) {
      // Show warning only once per build
      WidgetsBinding.instance.addPostFrameCallback((_) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              "Warning: This plan has no main entrance. Cannot add entrance automatically.",
            ),
            backgroundColor: Colors.orange,
            duration: Duration(seconds: 4),
          ),
        );
      });
    }

    List<dynamic> selectedPlanDoors = selectedPlan['doors'] ?? [];
    Map<String, dynamic>? boundary =
        selectedPlan['boundary'] ??
        {'min_x': 0, 'min_y': 0, 'max_x': 100, 'max_y': 100};
    roomGaps = List<Map<String, dynamic>>.from(selectedPlan['room_gaps'] ?? []);
    validation = Map<String, dynamic>.from(selectedPlan['validation'] ?? {});

    Map<String, dynamic>? planSizeData = selectedPlan['plan_size_data'];
    String planDimensions = 'N/A';
    if (planSizeData != null) {
      double length = (planSizeData['length'] as num?)?.toDouble() ?? 0.0;
      double width = (planSizeData['width'] as num?)?.toDouble() ?? 0.0;
      planDimensions =
          '${length.toStringAsFixed(1)} ft x ${width.toStringAsFixed(1)} ft';
    }

    return Scaffold(
   appBar: AppBar(
  title: Text(
    'Smart 2D House Plan Generator',
    style: TextStyle(
      fontSize: 22,
      fontWeight: FontWeight.bold,
      color: Colors.white,
    ),
  ),
  centerTitle: true,
  flexibleSpace: Container(
    decoration: BoxDecoration(
      gradient: LinearGradient(
        colors: [
          Colors.black87,
          Colors.blueGrey.shade900,
          Colors.indigo.shade800,
        ],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
    ),
  ),
  actions: [
    IconButton(
      icon: Icon(Icons.exit_to_app, color: Colors.white, size: 28),
      tooltip: 'Exit',
      onPressed: () {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => SplashPage()),
        );
      },
    ),
  ],
),

      body: Padding(
        padding: EdgeInsets.all(16.0),
        child: ListView(
          children: [
            Text(
              'Select Lifestyle:',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            DropdownButton<String>(
              value: selectedLifestyle,
              isExpanded: true,
              items: lifestyleRooms.keys
                  .map(
                    (value) => DropdownMenuItem(
                      value: value,
                      child: Text(value, style: TextStyle(fontSize: 16)),
                    ),
                  )
                  .toList(),
              onChanged: (newValue) {
                setState(() {
                  selectedLifestyle = newValue!;
                  initializeRoomControllers();

                  // Clear previously generated plan data
                  generatedPlans = [];
                  selectedPlanIndex = 0;
                  roomGaps = [];
                  validation = {};
                });
              },
            ),
            SizedBox(height: 20),
            for (var room in lifestyleRooms[selectedLifestyle]!)
              Card(
                margin: EdgeInsets.symmetric(vertical: 8),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                elevation: 4,
                child: Padding(
                  padding: EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        room,
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      SizedBox(height: 8),
                      Row(
                        children: [
                          Expanded(
                            child: TextFormField(
                              controller: roomControllers[room]!['count'],
                              decoration: InputDecoration(
                                labelText: 'Count',
                                border: OutlineInputBorder(),
                                filled: true,
                                fillColor: Colors.blue.shade50,
                              ),
                              keyboardType: TextInputType.number,
                            ),
                          ),
                          SizedBox(width: 8),
                          Expanded(
                            child: TextFormField(
                              controller: roomControllers[room]!['length'],
                              decoration: InputDecoration(
                                labelText: 'Length(5ft-30ft)',
                                border: OutlineInputBorder(),
                                filled: true,
                                fillColor: Colors.blue.shade50,
                              ),
                              keyboardType: TextInputType.number,
                            ),
                          ),
                          SizedBox(width: 8),
                          Expanded(
                            child: TextFormField(
                              controller: roomControllers[room]!['width'],
                              decoration: InputDecoration(
                                labelText: 'Width(5ft-25ft)',
                                border: OutlineInputBorder(),
                                filled: true,
                                fillColor: Colors.blue.shade50,
                              ),
                              keyboardType: TextInputType.number,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            SizedBox(height: 20),
            GradientButton(
              text: 'Add Room Data',
              onPressed: addRoomDataToBackend,
              colors: [
                Colors.indigo.shade700,
                Colors.blue.shade400,
                Colors.cyan.shade200,
              ],
            ),
            SizedBox(height: 16),
            GradientButton(
              text: isGenerating ? 'Generating...' : 'Generate House Plan',
              onPressed: isGenerating ? null : generatePlansFromBackend,
              colors: [
                Colors.indigo.shade700,
                Colors.blue.shade400,
                Colors.cyan.shade200,
              ],
            ),
            if (generatedPlans.isNotEmpty) ...[
              SizedBox(height: 20),
              Text(
                'Select Plan:',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              DropdownButton<int>(
                value: selectedPlanIndex,
                items: List.generate(
                  generatedPlans.length,
                  (i) =>
                      DropdownMenuItem(value: i, child: Text('Plan ${i + 1}')),
                ),
                onChanged: (newIndex) =>
                    setState(() => selectedPlanIndex = newIndex!),
              ),
              if (planSizeData != null) ...[
                SizedBox(height: 10),
                Card(
                  margin: EdgeInsets.symmetric(vertical: 8),
                  elevation: 3,
                  color: Colors.blue.shade50,
                  child: Padding(
                    padding: EdgeInsets.all(12.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Full Plan Size:',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Colors.indigo.shade800,
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          planDimensions,
                          style: TextStyle(fontSize: 18, color: Colors.black87),
                        ),
                      ],
                    ),
                  ),
                ),
                SizedBox(height: 10),
              ],
              Text(
                'Generated House Plan:',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.black,
                ),
              ),
              SizedBox(height: 10),
              RepaintBoundary(
                key: canvasKey,
                child: InteractiveViewer(
                  panEnabled: true,
                  scaleEnabled: true,
                  minScale: 0.5,
                  maxScale: 4.0,
                  child: HousePlanCanvas(
                    rooms: selectedPlanRooms,
                    doors: selectedPlanDoors,
                    boundary: boundary,
                    roomGaps: roomGaps,
                  ),
                ),
              ),
              SizedBox(height: 10),
              GradientButton(
                text: 'Download Plan',
                onPressed: captureAndSaveCanvas,
                colors: [Colors.green.shade700, Colors.lightGreen.shade400],
              ),
              SizedBox(height: 20), // spacing
              

              if (validation.isNotEmpty) ...[
                SizedBox(height: 16),
                Card(
                  color: Colors.white.withOpacity(0.9),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "Validation Results",
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          "Connectivity: ${validation['connectivity']?['is_connected'] ?? 'Unknown'}",
                          style: TextStyle(fontSize: 14),
                        ),
                        if (validation['connectivity']?['unreachable_rooms']
                                ?.isNotEmpty ??
                            false)
                          Text(
                            "Unreachable Rooms:\n${(validation['connectivity']['unreachable_rooms'] as List).map((room) => room['name']) // <-- only the name
                            .join(', ')}\n\n"
                            "These rooms cannot be directly connected, so add corridors in an appropriate way according to room gaps.",
                            style: TextStyle(fontSize: 14, color: Colors.red),
                          ),
                      ],
                    ),
                  ),
                ),
              ],
              if (roomGaps.isNotEmpty) ...[
                SizedBox(height: 10),
                Card(
                  color: Colors.white.withOpacity(0.9),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "Room Gaps (Path/Distance)",
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                        SizedBox(height: 4),
                        Column(
                          children: roomGaps.map((g) {
                            return Text(
                              "${g['room1']} ↔ ${g['room2']} : ${g['distance_ft'].toStringAsFixed(1)} ft",
                              style: TextStyle(fontSize: 14),
                            );
                          }).toList(),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ],
          ],
        ),
      ),
    );
  }
}

class GradientButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final List<Color> colors;

  const GradientButton({
    Key? key,
    required this.text,
    required this.onPressed,
    required this.colors,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 50,
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: colors),
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: colors.last.withOpacity(0.5),
            offset: Offset(0, 3),
            blurRadius: 6,
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onPressed,
          borderRadius: BorderRadius.circular(12),
          child: Center(
            child: Text(
              text,
              style: TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class HousePlanCanvas extends StatelessWidget {
  final List<dynamic> rooms;
  final List<dynamic> doors;
  final Map<String, dynamic>? boundary;
  final List<Map<String, dynamic>> roomGaps;
  final double scale;

  const HousePlanCanvas({
    Key? key,
    required this.rooms,
    required this.doors,
    this.boundary,
    required this.roomGaps,
    this.scale = 10.0,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    double maxWidth =
        rooms.fold(0.0, (prev, r) {
              double rx = (r['x'] as num?)?.toDouble() ?? 0.0;
              double rw = (r['width'] as num?)?.toDouble() ?? 10.0;
              return (rx + rw) > prev ? (rx + rw) : prev;
            }) *
            scale +
        20;
    double maxHeight =
        rooms.fold(0.0, (prev, r) {
              double ry = (r['y'] as num?)?.toDouble() ?? 0.0;
              double rh = (r['length'] as num?)?.toDouble() ?? 10.0;
              return (ry + rh) > prev ? (ry + rh) : prev;
            }) *
            scale +
        20;

    if (boundary != null) {
      double minX = (boundary!['min_x'] as num?)?.toDouble() ?? 0.0;
      double minY = (boundary!['min_y'] as num?)?.toDouble() ?? 0.0;
      double maxX = (boundary!['max_x'] as num?)?.toDouble() ?? 100.0;
      double maxY = (boundary!['max_y'] as num?)?.toDouble() ?? 100.0;

      double width = (maxX - minX) * scale + 20;
      double height = (maxY - minY) * scale + 20;

      maxWidth = width > maxWidth ? width : maxWidth;
      maxHeight = height > maxHeight ? height : maxHeight;
    }

    return Container(
      width: maxWidth.clamp(300.0, double.infinity),
      height: maxHeight.clamp(300.0, double.infinity),
      color: Colors.white,
      child: CustomPaint(
        painter: HousePlanPainter(rooms, doors, boundary, roomGaps, scale),
      ),
    );
  }
}

class HousePlanPainter extends CustomPainter {
  final List<dynamic> rooms;
  final List<dynamic> doors;
  final Map<String, dynamic>? boundary;
  final List<Map<String, dynamic>> roomGaps;
  final double scale;

  // NEW CONSTANT: Defines the minimum path width used in backend for connectivity
  static const double GAP_PATH_UNITS = 3.0;
  // Constant used to overdraw the wall or path for door opening
  static const double WALL_THICKNESS_OVERDRAW = 6.0;

  HousePlanPainter(
    this.rooms,
    this.doors,
    this.boundary,
    this.roomGaps,
    this.scale,
  );

  // Helper function to check if a door's center lies on a visualized gap line
  bool _isPathDoor(Map<String, dynamic> door, List<Map<String, dynamic>> gaps) {
    double doorWorldX = (door['x'] as num?)?.toDouble() ?? 0.0;
    double doorWorldY = (door['y'] as num?)?.toDouble() ?? 0.0;

    
    const double TOLERANCE = GAP_PATH_UNITS / 2;

    for (var gap in gaps) {
      double gx1 = (gap['x1'] as num?)?.toDouble() ?? 0.0;
      double gy1 = (gap['y1'] as num?)?.toDouble() ?? 0.0;
      double gx2 = (gap['x2'] as num?)?.toDouble() ?? 0.0;
      double gy2 = (gap['y2'] as num?)?.toDouble() ?? 0.0;
      String type = gap['type'] as String? ?? 'H';
      double distance = (gap['distance_ft'] as num?)?.toDouble() ?? 0.0;

      // We only care about gaps that are >= 3ft (i.e., the forced paths)
      if (distance < GAP_PATH_UNITS - 0.1) continue;

      if (type == 'H') {
        
        double lineY = gy1;

        if ((doorWorldY - lineY).abs() < TOLERANCE &&
            doorWorldX >= math.min(gx1, gx2) &&
            doorWorldX <= math.max(gx1, gx2)) {
          return true;
        }
      } else if (type == 'V') {
        
        double lineX = gx1;

        if ((doorWorldX - lineX).abs() < TOLERANCE &&
            doorWorldY >= math.min(gy1, gy2) &&
            doorWorldY <= math.max(gy1, gy2)) {
          return true;
        }
      }
    }
    return false;
  }
  

  

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..color = Colors.blue;

    final textPainter = TextPainter(
      textAlign: TextAlign.center,
      textDirection: TextDirection.ltr,
    );

    double offset = 10.0;

    // 1. Exterior Boundary Drawing
    if (boundary != null) {
      double minX = (boundary!['min_x'] as num?)?.toDouble() ?? 0.0;
      double minY = (boundary!['min_y'] as num?)?.toDouble() ?? 0.0;
      double maxX = (boundary!['max_x'] as num?)?.toDouble() ?? 100.0;
      double maxY = (boundary!['max_y'] as num?)?.toDouble() ?? 100.0;

      canvas.drawRect(
        Rect.fromLTWH(
          minX * scale + offset,
          minY * scale + offset,
          (maxX - minX) * scale,
          (maxY - minY) * scale,
        ),
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 3
          ..color = Colors.black,
      );
    }

    // 2. Room Drawing (Walls and Labels)
    for (var room in rooms) {
      double x = (room['x'] as num?)?.toDouble() ?? 0.0;
      double y = (room['y'] as num?)?.toDouble() ?? 0.0;
      double width = (room['width'] as num?)?.toDouble() ?? 10.0;
      double height = (room['length'] as num?)?.toDouble() ?? 10.0;

   Color roomColor = parseColor(room['color']?.toString());

  // Scale coordinates
  x = x * scale + offset;
  y = y * scale + offset;
  width *= scale;
  height *= scale;

  Rect rect = Rect.fromLTWH(x, y, width, height);

  // Fill room area
  if (room['is_entrance'] == true) {
    canvas.drawRect(
      rect,
      Paint()..color = Colors.red.shade200.withOpacity(0.75),
    );
  } 
  else if (room['is_corridor'] == true || room['room'] == 'Corridor') {
    
    canvas.drawRect(
      rect,
      Paint()..color = roomColor,   
    );

    
    canvas.drawRect(
      rect,
      Paint()
        ..color = Colors.grey.shade400.withOpacity(0.3)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.0,
    );
  } 
  else if (room['room'] != 'Roof' && room['room'] != 'Plan Size') {
    // Normal rooms - light fill
    canvas.drawRect(
      rect,
      Paint()..color = roomColor.withOpacity(0.22),
    );
  }

      // Draw Room Walls/Boundary
      canvas.drawRect(rect, paint);

      // Internal Door/Window Symbols (This section remains mostly unchanged)
      if (room['door_direction'] != null) {
        String dir = room['door_direction'].toString();
        double doorX = x + width / 2;
        double doorY = y;
        double doorLen = 12.0;
        double doorThickness = 4.0;

        switch (dir) {
          case 'N':
            doorY = y;
            doorX = x + width / 2;
            break;
          case 'S':
            doorY = y + height;
            doorX = x + width / 2;
            break;
          case 'E':
            doorX = x + width;
            doorY = y + height / 2;
            break;
          case 'W':
            doorX = x;
            doorY = y + height / 2;
            break;
        }

        bool isMainEntrance =
            (room['room'] == 'Main Entrance') || (room['is_entrance'] == true);

        if (isMainEntrance) {
          Rect doorRect;
          if (dir == 'N' || dir == 'S') {
            doorRect = Rect.fromCenter(
              center: Offset(doorX, doorY),
              width: doorLen * 2,
              height: doorThickness,
            );
          } else {
            doorRect = Rect.fromCenter(
              center: Offset(doorX, doorY),
              width: doorThickness,
              height: doorLen * 2,
            );
          }

          canvas.drawRect(
            doorRect,
            Paint()
              ..style = PaintingStyle.fill
              ..color = Colors.brown.shade800,
          );
        } else {
          canvas.drawCircle(
            Offset(doorX, doorY),
            3,
            Paint()..color = Colors.brown,
          );
        }
      }

      // ... (Window Drawing - unchanged)
      if (room['window_direction'] != null) {
        String wdir = room['window_direction'].toString();
        double windowX = x + width / 2;
        double windowY = y + height / 2;
        double windowLen = 15.0;

        switch (wdir) {
          case 'N':
            windowY = y;
            break;
          case 'S':
            windowY = y + height;
            break;
          case 'E':
            windowX = x + width;
            break;
          case 'W':
            windowX = x;
            break;
        }

        if (wdir == 'N' || wdir == 'S') {
          canvas.drawLine(
            Offset(windowX - windowLen / 2, windowY),
            Offset(windowX + windowLen / 2, windowY),
            Paint()
              ..color = Colors.lightBlue
              ..strokeWidth = 2,
          );
          canvas.drawLine(
            Offset(windowX - windowLen / 4, windowY),
            Offset(windowX + windowLen / 4, windowY),
            Paint()
              ..color = Colors.lightBlue.shade800
              ..strokeWidth = 4,
          );
        } else {
          canvas.drawLine(
            Offset(windowX, windowY - windowLen / 2),
            Offset(windowX, windowY + windowLen / 2),
            Paint()
              ..color = Colors.lightBlue
              ..strokeWidth = 2,
          );
          canvas.drawLine(
            Offset(windowX, windowY - windowLen / 4),
            Offset(windowX, windowY + windowLen / 4),
            Paint()
              ..color = Colors.lightBlue.shade800
              ..strokeWidth = 4,
          );
        }
      }

      // Room Labels
      if (room['room'] != null && room['room'] != 'Plan Size') {
        textPainter.text = TextSpan(
          text:
              "${room['room']} (${(room['length'] as num?)?.toStringAsFixed(1)}x${(room['width'] as num?)?.toStringAsFixed(1)} ft)",
          style: const TextStyle(
            fontSize: 12,
            color: Colors.black,
            fontWeight: FontWeight.bold,
          ),
        );

        textPainter.layout(minWidth: 0, maxWidth: width.clamp(0.0, 200.0));

        textPainter.paint(
          canvas,
          Offset(
            x + width / 2 - textPainter.width / 2,
            y + height / 2 - textPainter.height / 2,
          ),
        );
      }
    }

    
    
    
    // 4. Inter-Room Door Drawing
for (var door in doors) {
  double dx = (door['x'] as num?)?.toDouble() ?? 0.0;
  double dy = (door['y'] as num?)?.toDouble() ?? 0.0;
  String direction = door['direction'] as String? ?? 'H';
  double doorLengthInUnits = (door['length'] as num?)?.toDouble() ?? 3.0;

  bool isPathDoor = _isPathDoor(door, roomGaps);

  dx = dx * scale + offset;
  dy = dy * scale + offset;
  double doorLength = doorLengthInUnits * scale;
  double swingRadius = doorLength * 0.5;

  // === NEW LOGIC ===
  if (!isPathDoor) {
    // Normal wall door → draw white/clear opening to cut the wall
    final doorGapPaint = Paint()
      ..style = PaintingStyle.fill
      ..color = Colors.white;

    Rect doorOpeningRect;
    if (direction == 'H') {
      doorOpeningRect = Rect.fromCenter(
        center: Offset(dx, dy),
        width: WALL_THICKNESS_OVERDRAW,
        height: doorLength + WALL_THICKNESS_OVERDRAW,
      );
    } else {
      doorOpeningRect = Rect.fromCenter(
        center: Offset(dx, dy),
        width: doorLength + WALL_THICKNESS_OVERDRAW,
        height: WALL_THICKNESS_OVERDRAW,
      );
    }
    canvas.drawRect(doorOpeningRect, doorGapPaint);
  }


  // Draw the door leaf (swing arc) for ALL doors
  final doorLeafPaint = Paint()
    ..color = Colors.brown.shade700
    ..style = PaintingStyle.stroke
    ..strokeWidth = 2.0;   // slightly thicker for better visibility

  Path swingPath = Path();
  swingPath.moveTo(dx, dy);

  if (direction == 'H') {
    // Horizontal wall / path
    swingPath.arcTo(
      Rect.fromCircle(center: Offset(dx, dy), radius: swingRadius),
      math.pi / 2,
      -math.pi / 2,
      false,
    );
  } else {
    // Vertical wall / path
    swingPath.arcTo(
      Rect.fromCircle(center: Offset(dx, dy), radius: swingRadius),
      math.pi,
      math.pi / 2,
      false,
    );
  }
  canvas.drawPath(swingPath, doorLeafPaint);

  // Optional: small door frame / hinge line for better look
  canvas.drawLine(
    Offset(dx, dy),
    direction == 'H' 
        ? Offset(dx, dy - doorLength * 0.4)
        : Offset(dx - doorLength * 0.4, dy),
    Paint()..color = Colors.brown.shade800..strokeWidth = 1.5,
  );
}
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => true;
}

Color parseColor(String? colorStr) {
  if (colorStr == null || colorStr.isEmpty) {
    return Colors.grey;
  }

  colorStr = colorStr.trim();

  
  if (colorStr.startsWith('rgba')) {
    try {
      String inner = colorStr.substring(5, colorStr.length - 1).trim();
      List<String> parts = inner.split(',').map((e) => e.trim()).toList();

      if (parts.length == 4) {
        int r = int.parse(parts[0]);
        int g = int.parse(parts[1]);
        int b = int.parse(parts[2]);
        double a = double.parse(parts[3]);

        return Color.fromRGBO(r, g, b, a);
      }
    } catch (e) {
      print("RGBA parsing error for $colorStr: $e");
    }
  }

  // Handle hex format (old support)
  else if (colorStr.startsWith('#')) {
    String hex = colorStr.substring(1);
    if (hex.length == 6) {
      return Color(int.parse(hex, radix: 16) + 0xFF000000);
    } else if (hex.length == 8) {
      return Color(int.parse(hex, radix: 16));
    }
  }

  return Colors.grey; // fallback
}