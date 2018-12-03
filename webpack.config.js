const path = require('path');

module.exports = {
  entry: './assets/index.js',
	module: {
		rules: [
			{
				test: /\.(js|jsx)$/,
				exclude: /node_modules/,
				use: ['babel-loader']
			},
			{
        test: /\.css$/,
        use: ["style-loader", "css-loader"]
			}
		]
	},
	resolve: {
		extensions: ['*', '.js', '.jsx']
	},
  output: {
    path: path.resolve(__dirname, 'pm/static'),
    filename: 'bundle.js'
  }
};

