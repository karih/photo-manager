
app.filter('bytes', function() {
	return function(bytes, precision) {
		if (isNaN(parseFloat(bytes)) || !isFinite(bytes)) return '-';
		if (bytes === 0) return '0';
		if (typeof precision === 'undefined') precision = 1;
		var units = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'],
			number = Math.floor(Math.log(bytes) / Math.log(1024));
		return (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision) +  ' ' + units[number];
	}
});

app.filter('truncate_filename', function() {
	return function(str, len) {
		if (typeof(str) === "undefined") {
			return str;
		} else if (str.length <= len) {
			return str;
		} else {
			var bf = Math.floor(len/2)-1;
			var ef = Math.ceil(len/2)-2;

			return str.substring(0,bf) + "..." + str.substring(str.length-ef);
		}
	}
});

app.filter('truncate_filepath', function() {
	return function(str, len, filename) {
		if (typeof(str) === "undefined") {
			return str;
		} else if (str.length - filename.length <= len) {
			return str.substring(0, str.length-filename.length);
		} else {
			var start = str.length - filename.length - len;
			return "..." + str.substring(start, str.length - filename.length);
		}
	}
});

app.filter('exposure', ['$filter', function($filter) {
	return function(v) {
		if (v < 1) {
			v = 1 / v;
			return "1/" + $filter('number')(v, 0);
		} else {
			return $filter('number')(v, 1);
		}
	}
}]);

app.filter('aperture', ['$filter', function($filter) {
	return function(v) {
		return "f/" + $filter('number')(v, 1);
	}
}]);

