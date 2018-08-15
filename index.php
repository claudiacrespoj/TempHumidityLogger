<?php
// settings
// host, user and password settings
$host = "localhost";
$user = "logger2";
$password = "password";
$database = "temperatures";

//how many hours backwards do you want results to be shown in web page.
$hours = 1;

// make connection to database
$con = mysql_connect($host,$user,$password);
// select db
mysql_select_db($database,$con);

// sql command that selects all entires from current time and X hours backwards
//$sql="SELECT * FROM temperaturedata WHERE dateandtime >= (NOW() - INTERVAL $hours HOUR)";

//NOTE: If you want to show all entries from current date in web page uncomment line below by removing //
//$sql="select * from temperaturedata where date(dateandtime) = curdate();";

// set query to variable
//$temperatures = mysql_query($sql);

// create content to web-pagge
?>
<html>
<html lang="en">
<meta charset="UTF-8">
<head>
	<title>Air Compressor Monitoring System</title>
	<meta charset="utf-8" />
	<meta content="width=device-width, initial-scale=1" name="viewport" />
	<link href="/stylesheets/bootstrap.min.css" rel="stylesheet" /><script src="/javascripts/jquery.min.js"></script><script src="/javascripts/bootstrap.min.js"></script>
	<script type="text/javascript" src="/javascripts/jquery.min.js"></script>
	<script type="text/javascript" src="/javascripts/Chart.min.js"></script>
	<script type="text/javascript" src="/javascripts/linegraph.js"></script>
	<style>
			.chart-container {
				width: 640px;
				height: auto;
			}
	</style>
</head>
<body >
<p>&nbsp;</p>
<div class="container">
<p><img src="/images/carsan.png" alt="Logo" align= "left" ></p>
<p><img src="/images/NimBus.png" alt="Logo" align= "right" ></p>
<h1 style="text-align: center;"><strong><span style="font-size:34px;">
Air Compressor Monitoring System
</span></strong></h1>
<p>&nbsp;</p>
<head>
<style type="text/css">
table {
    width:100%;
}
table, th, td {
    border: 2px solid black;
}
</style>
</head>
<ul class="nav nav-tabs">
	<li class="active" style="text-align: center;"><a data-toggle="tab" href="#sensor1">SENSOR 1</a></li>
	<li style="text-align: center;"><a data-toggle="tab" href="#sensor2">SENSOR 2</a></li>
	<li style="text-align: center;"><a data-toggle="tab" href="#sensor3">SENSOR 3</a></li>
	<li style="text-align: center;"><a data-toggle="tab" href="#sensor4">SENSOR 4</a></li>
</ul>

<div class="tab-content">
<div class="tab-pane fade in active" id="sensor1">
<h3>Sensor 1 Readings</h3>

<p>&nbsp;</p>
<table width="600" border="1" cellpadding="1" cellspacing="1" align="center">
<tr>
<th>Date</th>
<th>Sensor</th>
<th>Temperature</th>
<th>Humidity</th>
<th>Dew point</th>
<tr>
<?php
     $sql="select * from temperaturedata where sensor = 'roomTemperature'AND dateandtime >= (NOW() - INTERVAL $hours HOUR)";
	// set query to variable
	$temperatures = mysql_query($sql);
        while($temperatura=mysql_fetch_assoc($temperatures)){
		
                echo "<tr>";
                echo "<td>".$temperatura['dateandtime']."</td>";
                echo "<td>".$temperatura['sensor']."</td>";
                echo "<td>".$temperatura['temperature']."</td>";
                echo "<td>".$temperatura['humidity']."</td>";
		echo "<td>".($temperatura['temperature']-((100-$temperatura['humidity'])/5))."</td>";
                echo "<tr>";
}
?>
</table>
</div>

<div class="tab-pane fade" id="sensor2">
<h3>Sensor 2 Readings</h3>

<p>&nbsp;</p>

<table width="600" border="1" cellpadding="1" cellspacing="1" align="center">
<tr>
<th>Date</th>
<th>Sensor</th>
<th>Temperature</th>
<th>Humidity</th>
<th>Dew point</th>
<tr>
<?php
     $sql="select * from temperaturedata where sensor = 'sensor2'AND dateandtime >= (NOW() - INTERVAL $hours HOUR)";
	// set query to variable
	$temperatures = mysql_query($sql);
        while($temperatura=mysql_fetch_assoc($temperatures)){
		
                echo "<tr>";
                echo "<td>".$temperatura['dateandtime']."</td>";
                echo "<td>".$temperatura['sensor']."</td>";
                echo "<td>".$temperatura['temperature']."</td>";
                echo "<td>".$temperatura['humidity']."</td>";
		echo "<td>".($temperatura['temperature']-((100-$temperatura['humidity'])/5))."</td>";
                echo "<tr>";
		
        }
?>
</table>
</div>

<div class="tab-pane fade" id="sensor3">
<h3>Sensor 3 Readings</h3>

<p>&nbsp;</p>

<table width="600" border="1" cellpadding="1" cellspacing="1" align="center">
<tr>
<th>Date</th>
<th>Sensor</th>
<th>Temperature</th>
<th>Humidity</th>
<th>Dew point</th>
<tr>
<?php
     $sql="select * from temperaturedata where sensor = 'sensor3'AND dateandtime >= (NOW() - INTERVAL $hours HOUR)";
	// set query to variable
	$temperatures = mysql_query($sql);
        while($temperatura=mysql_fetch_assoc($temperatures)){
		
                echo "<tr>";
                echo "<td>".$temperatura['dateandtime']."</td>";
                echo "<td>".$temperatura['sensor']."</td>";
                echo "<td>".$temperatura['temperature']."</td>";
                echo "<td>".$temperatura['humidity']."</td>";
		echo "<td>".($temperatura['temperature']-((100-$temperatura['humidity'])/5))."</td>";
                echo "<tr>";
		
        }
?>
</table>
</div>

<div class="tab-pane fade" id="sensor4">
<h3>Sensor 4</h3>
<?php 

?>

<p>&nbsp;</p>

	</tbody>
</table>
</div>
</html>