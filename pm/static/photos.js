
app.controller('PhotosOverviewCtrl', ['$scope', '$http', '$stateParams', '$state', '$document', '$filter', function($scope, $http, $stateParams, $state, $document, $filter) {
	console.log("PhotosOverviewCtrl(", $stateParams, ")")

	$scope.offset = $stateParams["offset"];
	$scope.limit = $stateParams["limit"];

	this.fetch = function() {
		//console.log("FETCHING ", $stateParams);
		$http.get('/api/photos', {params: $stateParams} ).success(function(data) {
			$scope.photos = data.photos;
			$scope.facets = data.facets;
			$scope.hits = data.results;
		});
	}

	$document.bind('keydown', function(event, args) {
		var new_state = JSON.parse(JSON.stringify($stateParams));
		if (event.keyCode == 39 && ($scope.offset + $scope.limit <= $scope.hits)) {
			new_state["offset"] = $scope.offset + $scope.limit;
			$state.go('photos.list', new_state);
		} else if (event.keyCode == 37) {
			new_state["offset"] = Math.max(0, $scope.offset - $scope.limit);
			$state.go('photos.list', new_state);
		}	
	});
	$scope.$on('$destroy', function() {
		$document.unbind('keydown');
	});

	this.uiOnParamsChanged = function (changedParams, $transition$) {
		//console.log("CHANGE IN STATE");
		/* state called again with changed parameters */
		angular.forEach(changedParams, function(value, key) {
			$stateParams[key] = value;
			$scope[key] = value;
		})
		this.fetch();
	};

	$scope.movePage = function(offset, limit) {
		var new_state = JSON.parse(JSON.stringify($stateParams));
		new_state["offset"] = offset;
		new_state["limit"] = limit;
		return $state.href('photos.list', new_state);
	}

	$scope.filter_fun = function(filter) {
		console.log("Generating filter function", filter);
		return function(value) {
			console.log("Moving states for filter ", filter, ". $stateParams: ", $stateParams);
			var new_state = JSON.parse(JSON.stringify($stateParams));
			new_state["offset"] = 0; 
			if (new_state[filter] == value) {
				new_state[filter] = null; // deselect
			} else {
				new_state[filter] = value; // select
			}
			$state.go("photos.list", new_state);
		}
	}

	$scope.singleHref = function(photo) {
		var new_state = JSON.parse(JSON.stringify($stateParams));
		new_state.id = photo.id;
		return $state.href("photos.details", new_state);
	}

	$scope.oneliner = function(photo) { return "P#" + photo.id };

	$scope.apertureFormatter = function(v) { return $filter('aperture')(v); }
	$scope.exposureFormatter = function(v) { return $filter('exposure')(v); }

	this.fetch();
}]);

app.controller('PhotoCtrl', ['$scope', '$http', '$stateParams', '$filter', function($scope, $http, $stateParams, $filter) {
	console.log("PhotoCtrl(", $stateParams, ")");	

	$scope.properties = [ 
		["aperture", "Aperture", $filter('aperture'), ],
		["exposure", "Exposure", $filter('exposure'), ],
		["date", "Date", function(v) { return v; }],
		["focal_length", "Focal Length", function(v) { return v; }],
		["focal_length_35", "Focal Length (35mm)", function(v) { return v; }],
		["iso", "ISO", function(v) { return v; }],
		["make", "Make", function(v) { return v; }],
		["model", "Model", function(v) { return v; }],
		["lens", "Lens", function(v) { return v; }],
	];

	console.log($scope.properties);
	
	$scope.changeFile = function(v) {
		console.log("RASS");
		$http.put('/api/photo/' + $stateParams["id"], {file_id: v}).success(function(data) {
			$scope.photo = data.photo;
		});
	}

	$http.get('/api/photo/' + $stateParams["id"]).success(function(data) {
		$scope.photo = data.photo;
	});
}]);
