app.controller('PhotosOverviewCtrl', ['$scope', '$http', '$stateParams', '$state', '$document', function($scope, $http, $stateParams, $state, $document) {
	console.log("PhotosOverviewCtrl(" + $stateParams + ")")

	$scope.limit = $stateParams["limit"];
	$scope.offset = $stateParams["offset"];

	this.fetch = function(offset, limit) {
		console.log("FETCHING");
		$http.get('/api/photos', { params: {offset: offset, limit: limit} }).success(function(data) {
			$scope.photos = data.photos;
			$scope.facets = data.facets;
		});
	}

	this.uiOnParamsChanged = function (changedParams, $transition$) {
		/* state called again with changed parameters */
		$scope.offset = changedParams.hasOwnProperty("offset") ? changedParams.offset : $scope.offset;
		$scope.limit  = changedParams.hasOwnProperty("limit")  ? changedParams.limit : $scope.limit;
		this.fetch($scope.offset, $scope.limit);
	};

	this.fetch($scope.offset, $scope.limit);
}]);

app.controller('PhotoCtrl', ['$scope', '$http', '$stateParams', function($scope, $http, $stateParams) {
	console.log("PhotoCtrl(" + $stateParams["id"] + ")");	

	$http.get('/api/photo/' + $stateParams["id"]).success(function(data) {
		$scope.photo = data.photo;
	});
}]);
